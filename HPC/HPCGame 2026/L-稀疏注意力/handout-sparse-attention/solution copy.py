import torch
import triton
import triton.language as tl

@triton.autotune(
    configs=[
        triton.Config({}, num_warps=4, num_stages=2),
        triton.Config({}, num_warps=4, num_stages=3),
        triton.Config({}, num_warps=8, num_stages=2),
        triton.Config({}, num_warps=8, num_stages=3),
    ],
    key=["D_H", "BS", "G"],
)
@triton.jit
def _sparse_attention_kernel(
    Q, K, V, Index, Out,
    stride_qb, stride_qh, stride_qn, stride_qd,
    stride_kb, stride_kh, stride_km, stride_kd,
    stride_vb, stride_vh, stride_vm, stride_vd,
    stride_ib, stride_ih, stride_in, stride_ik,
    stride_ob, stride_oh, stride_on, stride_od,
    sm_scale,
    M,
    D_H: tl.constexpr,
    TOP_K: tl.constexpr,
    BS: tl.constexpr,
    G: tl.constexpr,
    BLOCK_D: tl.constexpr,
    BLOCK_BS: tl.constexpr,
    BLOCK_G: tl.constexpr,
):
    # Program ID
    pid_n = tl.program_id(0)   # Query sequence index
    pid_hk = tl.program_id(1)  # KV head index
    pid_b = tl.program_id(2)   # Batch index

    # Offsets
    offs_g = tl.arange(0, BLOCK_G)
    offs_d = tl.arange(0, BLOCK_D)
    offs_bs = tl.arange(0, BLOCK_BS)

    # Load Q for the entire GQA group: [BLOCK_G, BLOCK_D]
    # Each program handles g heads for one query token
    q_base = Q + pid_b * stride_qb + pid_hk * G * stride_qh + pid_n * stride_qn
    q_ptrs = q_base + offs_g[:, None] * stride_qh + offs_d[None, :] * stride_qd
    q_mask = (offs_g[:, None] < G) & (offs_d[None, :] < D_H)
    q = tl.load(q_ptrs, mask=q_mask, other=0.0).to(tl.float16)

    # Index base pointer for current token and current KV head
    idx_base = Index + pid_b * stride_ib + pid_hk * stride_ih + pid_n * stride_in
    
    # Initialize online softmax parameters
    m_i = tl.full([BLOCK_G], -float('inf'), dtype=tl.float32)
    l_i = tl.zeros([BLOCK_G], dtype=tl.float32)
    acc = tl.zeros([BLOCK_G, BLOCK_D], dtype=tl.float32)

    # Loop over top_K sparse blocks
    for tk in range(0, TOP_K):
        # Load block index from Index tensor
        block_idx = tl.load(idx_base + tk * stride_ik)
        valid_block = block_idx != -1
        start_m = tl.where(valid_block, block_idx, 0) * BS

        # Load shared K and V blocks for this group
        # K, V shape: [BS, D_H]
        k_base = K + pid_b * stride_kb + pid_hk * stride_kh + start_m * stride_km
        v_base = V + pid_b * stride_vb + pid_hk * stride_vh + start_m * stride_vm

        k_ptrs = k_base + offs_bs[:, None] * stride_km + offs_d[None, :] * stride_kd
        v_ptrs = v_base + offs_bs[:, None] * stride_vm + offs_d[None, :] * stride_vd

        kv_mask = valid_block & (offs_bs[:, None] < BS) & ((start_m + offs_bs[:, None]) < M) & (offs_d[None, :] < D_H)
        k = tl.load(k_ptrs, mask=kv_mask, other=0.0)
        v = tl.load(v_ptrs, mask=kv_mask, other=0.0)

        # Compute attention scores: [G, BS] = [G, D] @ [D, BS]
        qk = tl.dot(q, tl.trans(k).to(tl.float16)) * sm_scale

        # Apply Causal Mask & Block Boundary Mask
        # j = start_m + offset, must be <= i (pid_n)
        mask = valid_block & (offs_g[:, None] < G) & (offs_bs[None, :] < BS) & ((start_m + offs_bs[None, :]) <= pid_n)
        qk = tl.where(mask, qk, -float('inf'))

        # Online Softmax update
        m_ij = tl.max(qk, axis=1)
        m_next = tl.maximum(m_i, m_ij)

        # exp(m_i - m_next)
        alpha = tl.exp(m_i - m_next)
        # p = exp(score - m_next)
        p = tl.exp(qk - m_next[:, None])

        # Update denominator
        l_i = l_i * alpha + tl.sum(p, axis=1)

        # Update numerator (accumulator): [G, D] = [G, BS] @ [BS, D]
        acc = acc * alpha[:, None] + tl.dot(p.to(tl.float16), v.to(tl.float16))

        m_i = m_next

    # Normalize accumulator
    acc = tl.where(l_i[:, None] > 0, acc / l_i[:, None], 0.0)
    
    # Store result for the GQA group: [G, D_H]
    out_base = Out + pid_b * stride_ob + pid_hk * G * stride_oh + pid_n * stride_on
    out_ptrs = out_base + offs_g[:, None] * stride_oh + offs_d[None, :] * stride_od
    tl.store(out_ptrs, acc.to(tl.float16), mask=q_mask)

def sparse_attention(q, k, v, index, block_size, sm_scale):
    """
    High-performance Sparse Attention using Triton.
    
    Args:
        q: [B, h_q, N, d_h]
        k: [B, h_k, M, d_h]
        v: [B, h_k, M, d_h]
        index: [B, h_k, N, top_k]
        block_size: int (bs)
        sm_scale: float
    """
    B, H_Q, N, D_H = q.shape
    _, H_K, M, _ = k.shape
    _, _, _, top_K = index.shape
    
    # Group size for GQA
    G = H_Q // H_K
    
    # Create output tensor
    out = torch.empty_like(q)
    
    # Pre-calculate tiling parameters
    # tl.dot requires dimensions to be power of 2 and >= 16
    if D_H & (D_H - 1) != 0:
        raise ValueError("D_H must be power of 2 for tl.dot")
    if block_size & (block_size - 1) != 0:
        raise ValueError("block_size must be power of 2 for tl.dot")
    BLOCK_D = D_H
    BLOCK_BS = block_size
    BLOCK_G = G

    # Launch grid: one program per query token per KV head
    # Each program handles G query heads
    grid = (N, H_K, B)
    
    _sparse_attention_kernel[grid](
        q, k, v, index, out,
        q.stride(0), q.stride(1), q.stride(2), q.stride(3),
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        index.stride(0), index.stride(1), index.stride(2), index.stride(3),
        out.stride(0), out.stride(1), out.stride(2), out.stride(3),
        sm_scale,
        M,
        D_H=D_H,
        TOP_K=top_K,
        BS=block_size,
        G=G,
        BLOCK_D=BLOCK_D, BLOCK_BS=BLOCK_BS, BLOCK_G=BLOCK_G,
    )
    
    return out