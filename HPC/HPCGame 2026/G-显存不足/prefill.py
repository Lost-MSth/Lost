# prefill.py
import argparse
import inspect
import json
import os
import sys
from typing import Any, Dict, List

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

# AMD ROCm flash-attn switch
os.environ.setdefault("FLASH_ATTENTION_TRITON_AMD_ENABLE", "TRUE")

# ---------------------------
# Args: support both --model and --model_path
# ---------------------------
parser = argparse.ArgumentParser(description="Prefill Qwen3-32B BF16 with CPU offload")
parser.add_argument("--model", "--model_path", dest="model_path", required=True)
args = parser.parse_args()

torch.set_grad_enabled(False)
torch.cuda.init()

cuda = torch.device("cuda")
cpu = torch.device("cpu")

# Prefer flash sdp kernel if available
try:
    torch.backends.cuda.enable_flash_sdp(True)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(False)
except Exception:
    pass


# ---------------------------
# Locate layers / modules
# ---------------------------
def _get_layers(model: torch.nn.Module):
    if hasattr(model, "model"):
        inner = model.model
        for cand in ("layers", "h", "decoder_layers"):
            if hasattr(inner, cand):
                return getattr(inner, cand)
    for cand in ("layers", "h", "decoder_layers"):
        if hasattr(model, cand):
            return getattr(model, cand)
    raise RuntimeError("Unable to locate transformer layers")


def _maybe_get(module: torch.nn.Module, names: List[str]):
    for n in names:
        if hasattr(module, n):
            return getattr(module, n)
    return None


# ---------------------------
# Load tokenizer/model (NOT timed; interact starts timing after "ready")
# ---------------------------
tokenizer = AutoTokenizer.from_pretrained(args.model_path, use_fast=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id

# Load model (try flash_attention_2, fallback to sdpa/none)
model_kwargs = dict(dtype=torch.bfloat16, low_cpu_mem_usage=False)
try:
    model_kwargs["attn_implementation"] = "flash_attention_2"
    model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)
except TypeError:
    try:
        model_kwargs["attn_implementation"] = "sdpa"
        model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)
    except TypeError:
        model_kwargs.pop("attn_implementation", None)
        model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)

model.eval()
model.config.use_cache = False
model.config.pad_token_id = tokenizer.pad_token_id

root = model.model if hasattr(model, "model") else model
layers = _get_layers(model)

embed = _maybe_get(root, ["embed_tokens", "tok_embeddings"]) or model.get_input_embeddings()
final_norm = _maybe_get(root, ["norm", "final_layer_norm"])
lm_head = getattr(model, "lm_head", None) or model.get_output_embeddings()

if embed is None or lm_head is None:
    raise RuntimeError("Failed to locate embed/lm_head")

# Put light shared modules on GPU
embed.to(cuda)
if final_norm is not None:
    final_norm.to(cuda)

# Handle tied weights
tied = False
try:
    tied = hasattr(lm_head, "weight") and hasattr(embed, "weight") and (
        lm_head.weight.data_ptr() == embed.weight.data_ptr()
    )
except Exception:
    tied = False

if not tied:
    lm_head.to(cuda)
else:
    try:
        model.tie_weights()
    except Exception:
        pass

# Rotary embedding (optional)
rotary_emb = getattr(root, "rotary_emb", None)
rotary_params = None
if rotary_emb is not None:
    try:
        rotary_params = inspect.signature(rotary_emb.forward).parameters
    except Exception:
        rotary_params = None
    rotary_emb.to(cuda)


def _compute_position_embeddings(position_ids_1: torch.Tensor, hidden_states_1: torch.Tensor):
    if rotary_emb is None or rotary_params is None:
        return None
    kwargs: Dict[str, Any] = {}
    if "position_ids" in rotary_params:
        kwargs["position_ids"] = position_ids_1
    if "seq_len" in rotary_params:
        kwargs["seq_len"] = position_ids_1.shape[-1]
    if "hidden_states" in rotary_params:
        kwargs["hidden_states"] = hidden_states_1
    elif "x" in rotary_params:
        kwargs["x"] = hidden_states_1
    elif "inputs_embeds" in rotary_params:
        kwargs["inputs_embeds"] = hidden_states_1
    try:
        return rotary_emb(**kwargs) if kwargs else rotary_emb(position_ids_1)
    except Exception:
        try:
            return rotary_emb(position_ids_1)
        except Exception:
            return None


# ---------------------------
# Prebuild per-layer forward callables (minimal Python overhead)
# ---------------------------
layer_calls: List[Any] = []
layer_streamable: List[bool] = []

for layer in layers:
    params = inspect.signature(layer.forward).parameters
    has_pos_ids = "position_ids" in params
    has_pos_emb = "position_embeddings" in params
    has_past = "past_key_value" in params
    has_outattn = "output_attentions" in params
    has_use_cache = "use_cache" in params
    has_cache_pos = "cache_position" in params

    base_kwargs: Dict[str, Any] = {}
    if has_past:
        base_kwargs["past_key_value"] = None
    if has_outattn:
        base_kwargs["output_attentions"] = False
    if has_use_cache:
        base_kwargs["use_cache"] = False
    if has_cache_pos:
        base_kwargs["cache_position"] = None

    def _make_call(layer_ref, base_kwargs_ref, has_pos_ids_ref, has_pos_emb_ref):
        def _call(h, pos_ids, pos_emb):
            if has_pos_ids_ref and has_pos_emb_ref:
                out = layer_ref(h, position_ids=pos_ids, position_embeddings=pos_emb, **base_kwargs_ref)
            elif has_pos_ids_ref:
                out = layer_ref(h, position_ids=pos_ids, **base_kwargs_ref)
            elif has_pos_emb_ref:
                out = layer_ref(h, position_embeddings=pos_emb, **base_kwargs_ref)
            else:
                out = layer_ref(h, **base_kwargs_ref)
            return out[0] if isinstance(out, tuple) else out
        return _call

    layer_calls.append(_make_call(layer, base_kwargs, has_pos_ids, has_pos_emb))
    layer_streamable.append(True)


# ---------------------------
# Auto choose resident head/tail by VRAM budget (SAFETY_GB capped at 10 per your constraint)
# ---------------------------
def _layer_bytes(layer: torch.nn.Module) -> int:
    b = 0
    for p in layer.parameters(recurse=True):
        b += p.numel() * p.element_size()
    for _, buf in layer.named_buffers(recurse=True):
        if buf is not None:
            b += buf.numel() * buf.element_size()
    return b


layer_bytes = [_layer_bytes(l) for l in layers]
max_layer_b = max(layer_bytes) if layer_bytes else 0

free_b, _total_b = torch.cuda.mem_get_info()

SAFETY_GB = 9.3  # per your constraint
safety_b = SAFETY_GB * (1024**3)

# room for streamed layer + prefetched layer
budget_b = max(0, free_b - safety_b - 2 * max_layer_b)

prefix = [0]
for b in layer_bytes:
    prefix.append(prefix[-1] + b)

n_layers = len(layers)

def head_tail_cost(k: int) -> int:
    return prefix[k] + (prefix[n_layers] - prefix[n_layers - k])

best_k = 16
max_k = n_layers // 2
for k in range(0, max_k + 1):
    if head_tail_cost(k) <= budget_b:
        best_k = k

KEEP_HEAD = best_k
KEEP_TAIL = best_k

def _is_resident(i: int) -> bool:
    return i < KEEP_HEAD or i >= n_layers - KEEP_TAIL


# ---------------------------
# Streamed layer CPU state: pin weights + pointer-restore offload (no D2H copy)
# ---------------------------
class LayerCPUState:
    __slots__ = ("params", "cpu_params", "buf_owners", "buf_names", "cpu_bufs")

    def __init__(self, layer: torch.nn.Module):
        self.params = []
        self.cpu_params = []
        self.buf_owners = []
        self.buf_names = []
        self.cpu_bufs = []

        # Parameters
        for p in layer.parameters(recurse=True):
            if p.device.type != "cpu":
                p.data = p.data.to(cpu)
            if not p.data.is_pinned():
                p.data = p.data.pin_memory()
            self.params.append(p)
            self.cpu_params.append(p.data)

        # Buffers
        for name, buf in layer.named_buffers(recurse=True):
            if buf is None:
                continue
            if buf.device.type != "cpu":
                buf_cpu = buf.to(cpu)
            else:
                buf_cpu = buf
            if hasattr(buf_cpu, "is_pinned") and (not buf_cpu.is_pinned()):
                buf_cpu = buf_cpu.pin_memory()
            parent, _, bname = name.rpartition(".")
            owner = layer.get_submodule(parent) if parent else layer
            owner._buffers[bname] = buf_cpu
            self.buf_owners.append(owner)
            self.buf_names.append(bname)
            self.cpu_bufs.append(buf_cpu)

    def prefetch_to_cuda(self, stream: torch.cuda.Stream) -> torch.cuda.Event:
        with torch.cuda.stream(stream):
            for p, cpu_t in zip(self.params, self.cpu_params):
                p.data = cpu_t.to(cuda, non_blocking=True)
            for owner, bname, cpu_t in zip(self.buf_owners, self.buf_names, self.cpu_bufs):
                owner._buffers[bname] = cpu_t.to(cuda, non_blocking=True)
            evt = torch.cuda.Event()
            evt.record()
        return evt

    def restore_cpu_pointers(self):
        for p, cpu_t in zip(self.params, self.cpu_params):
            p.data = cpu_t
        for owner, bname, cpu_t in zip(self.buf_owners, self.buf_names, self.cpu_bufs):
            owner._buffers[bname] = cpu_t


layer_cpu_states: List[LayerCPUState | None] = [None] * n_layers

# Place layers: resident on GPU; others on CPU + pinned
for i, layer in enumerate(layers):
    if _is_resident(i):
        layer.to(cuda)
        layer_streamable[i] = False
    else:
        layer.to(cpu)
        layer_cpu_states[i] = LayerCPUState(layer)
        layer_streamable[i] = True


# ---------------------------
# Warmup (not timed)
# ---------------------------
def _warmup():
    try:
        with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            x = torch.zeros((1, 8), dtype=torch.long, device=cuda)
            h = embed(x)
            pos1 = torch.arange(8, device=cuda, dtype=torch.long).unsqueeze(0)
            pos_emb = _compute_position_embeddings(pos1, h[:1])
            for i in range(min(2, n_layers)):
                if layer_streamable[i]:
                    st = layer_cpu_states[i]
                    assert st is not None
                    evt = st.prefetch_to_cuda(torch.cuda.current_stream())
                    torch.cuda.current_stream().wait_event(evt)
                h = layer_calls[i](h, pos1.expand(1, -1), pos_emb)
                if layer_streamable[i]:
                    layer_cpu_states[i].restore_cpu_pointers()
            if final_norm is not None:
                h = final_norm(h)
            _ = lm_head(h)
        torch.cuda.synchronize()
    except Exception:
        pass

_warmup()

# Ready (timing starts after this line in interact.py)
print("ready", flush=True)


# ===========================
# Timed section
# ===========================
texts = json.loads(sys.stdin.readline())
N = len(texts)
if N == 0:
    sys.exit(0)

# Fast tokenize all texts at once
enc = tokenizer(texts, return_attention_mask=False)
ids_list: List[List[int]] = enc["input_ids"]
lengths = [len(x) for x in ids_list]
seq_tensors = [torch.tensor(x, dtype=torch.long) for x in ids_list]

# Bucketing to reduce padding waste
BUCKET = 128
buckets: Dict[int, List[int]] = {}
for i in range(N):
    L = lengths[i]
    bL = ((L + BUCKET - 1) // BUCKET) * BUCKET
    buckets.setdefault(bL, []).append(i)
for bL in buckets:
    buckets[bL].sort(key=lambda i: lengths[i], reverse=True)

# Constraints you specified
MAX_BATCH_SIZE = 8
MAX_BATCH_TOKENS = 65536  # uses padded tokens: bL * bs

# Caches
pos_ids_1_cache: Dict[int, torch.Tensor] = {}
pos_emb_cache: Dict[int, Any] = {}

# Batch storage (hidden stays on GPU)
batches_hidden: List[torch.Tensor] = []
batches_pos: List[torch.Tensor] = []
batches_posemb: List[Any] = []
batches_shift_labels: List[torch.Tensor] = []
batches_shift_mask: List[torch.Tensor] = []
batches_indices: List[List[int]] = []

with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    for bL in sorted(buckets.keys(), reverse=True):
        idxs = buckets[bL]
        j = 0

        # token-budget based bs limit
        max_bs_by_tok = max(1, MAX_BATCH_TOKENS // bL)

        # position ids cache (1, L) on GPU
        if bL not in pos_ids_1_cache:
            pos_ids_1_cache[bL] = torch.arange(bL, device=cuda, dtype=torch.long).unsqueeze(0)
        pos1 = pos_ids_1_cache[bL]

        while j < len(idxs):
            bs = min(MAX_BATCH_SIZE, max_bs_by_tok, len(idxs) - j)
            batch_idx = idxs[j : j + bs]
            j += bs

            # IMPORTANT: pinned CPU tensor -> true async H2D
            input_ids = torch.full(
                (bs, bL),
                tokenizer.pad_token_id,
                dtype=torch.long,
                pin_memory=True,
            )
            for r, ii in enumerate(batch_idx):
                s = seq_tensors[ii]
                input_ids[r, : s.numel()] = s

            # H2D async
            input_ids_gpu = input_ids.to(cuda, non_blocking=True)

            # embed + dropout (if present)
            h = embed(input_ids_gpu)
            if hasattr(root, "embed_dropout"):
                h = root.embed_dropout(h)
            elif hasattr(root, "dropout"):
                h = root.dropout(h)

            # batch position ids (view expand)
            pos = pos1.expand(bs, -1)

            # position embedding cache per length
            if bL not in pos_emb_cache:
                pos_emb_cache[bL] = _compute_position_embeddings(pos1, h[:1])
            pos_emb = pos_emb_cache[bL]

            # mask on GPU (avoid CPU compare + extra H2D)
            attn_mask = input_ids_gpu.ne(tokenizer.pad_token_id)

            # cache shift labels/mask on GPU to avoid any later H2D
            shift_labels = input_ids_gpu[:, 1:].contiguous()
            shift_mask = attn_mask[:, 1:]

            batches_hidden.append(h)
            batches_pos.append(pos)
            batches_posemb.append(pos_emb)
            batches_shift_labels.append(shift_labels)
            batches_shift_mask.append(shift_mask)
            batches_indices.append(batch_idx)

# Layer streaming with async prefetch + event
load_stream = torch.cuda.Stream()

# prefetch first streamed layer
next_evt = None
for i in range(n_layers):
    if layer_streamable[i]:
        st = layer_cpu_states[i]
        assert st is not None
        next_evt = st.prefetch_to_cuda(load_stream)
        break

with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    for li in range(n_layers):
        if layer_streamable[li]:
            if next_evt is not None:
                torch.cuda.current_stream().wait_event(next_evt)

        # prefetch next streamed layer
        next_evt = None
        for nj in range(li + 1, n_layers):
            if layer_streamable[nj]:
                stn = layer_cpu_states[nj]
                assert stn is not None
                next_evt = stn.prefetch_to_cuda(load_stream)
                break

        call = layer_calls[li]

        # run this layer across all batches
        for bi in range(len(batches_hidden)):
            batches_hidden[bi] = call(batches_hidden[bi], batches_pos[bi], batches_posemb[bi])

        # offload by pointer restore (no D2H)
        if layer_streamable[li]:
            layer_cpu_states[li].restore_cpu_pointers()

# Final norm + lm_head + loss (keep baseline numerics: logits.float())
loss_out = [0.0] * N

with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    for bi in range(len(batches_hidden)):
        h = batches_hidden[bi]
        if final_norm is not None:
            h = final_norm(h)

        logits = lm_head(h).float()
        shift_logits = logits[:, :-1, :]

        shift_labels = batches_shift_labels[bi]
        shift_mask = batches_shift_mask[bi]

        # Handle extremely short sequences defensively
        if shift_logits.numel() == 0:
            for idx in batches_indices[bi]:
                loss_out[idx] = 0.0
            continue

        loss_pt = F.cross_entropy(
            shift_logits.reshape(-1, shift_logits.size(-1)),
            shift_labels.reshape(-1),
            reduction="none",
        ).view_as(shift_labels)

        denom = shift_mask.sum(dim=1).clamp(min=1)
        loss_per = (loss_pt * shift_mask).sum(dim=1) / denom

        for idx, l in zip(batches_indices[bi], loss_per.tolist()):
            loss_out[idx] = float(l)

for i in range(N):
    print(loss_out[i], flush=True)
