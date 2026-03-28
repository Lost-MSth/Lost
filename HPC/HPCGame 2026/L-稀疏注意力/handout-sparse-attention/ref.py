import torch

def reference_sparse_attention(q, k, v, index, bs, sm_scale):
    """
    Reference implementation of Sparse Attention using PyTorch.
    
    Args:
        q: [B, h_q, N, d_h]
        k: [B, h_k, M, d_h]
        v: [B, h_k, M, d_h]
        index: [B, h_k, N, top_k] Int32 tensor containing block indices
        bs: Block size (int)
        sm_scale: Softmax scaling factor (float)
    
    Returns:
        out: [B, h_q, N, d_h]
    """
    B, h_q, N, d_h = q.shape
    _, h_k, M, _ = k.shape
    _, _, _, top_k = index.shape
    g = h_q // h_k # GQA Group size
    device = q.device

    # Output (fp16)
    out = torch.zeros_like(q)
    
    # Use float32 for high precision accumulation
    k_f = k.float()
    v_f = v.float()
    q_f = q.float()
    
    # 1. Iterate over KV heads (each h_k represents a GQA group)
    for hk_idx in range(h_k):
        # KV for current group [B, M, d_h]
        # Avoid repeat_interleave to save memory
        k_group = k_f[:, hk_idx, :, :] 
        v_group = v_f[:, hk_idx, :, :]
        
        # Q heads for this group [B, g, N, d_h]
        q_group = q_f[:, hk_idx*g : (hk_idx+1)*g, :, :]
        idx_group = index[:, hk_idx, :, :] # [B, N, top_k]

        # 2. Block processing along sequence dimension N
        chunk_size = 128 # Conservative chunk size for long sequences
        for i_start in range(0, N, chunk_size):
            i_end = min(i_start + chunk_size, N)
            cur_N = i_end - i_start
            
            # Current chunk Q and Index
            q_chunk = q_group[:, :, i_start:i_end, :] # [B, g, cur_N, d_h]
            idx_chunk = idx_group[:, i_start:i_end, :] # [B, cur_N, top_k]
            
            # 3. Generate Token Indices on the fly
            offsets = torch.arange(bs, device=device)
            # [B, cur_N, top_k, 1] + [bs] -> [B, cur_N, top_k * bs]
            t_idx = (idx_chunk.unsqueeze(-1) * bs + offsets).reshape(B, cur_N, top_k * bs)
            
            # 4. Gather K, V (Fancy Indexing)
            # Handle padding index -1
            mask_invalid = (t_idx < 0)
            t_idx_clamped = t_idx.clamp(min=0, max=M-1)
            
            # Batch index for gathering
            b_idx = torch.arange(B, device=device).view(B, 1, 1)
            # k_selected: [B, cur_N, top_k * bs, d_h]
            k_selected = k_group[b_idx, t_idx_clamped]
            v_selected = v_group[b_idx, t_idx_clamped]

            # 5. Compute Attention Scores
            # q_chunk: [B, g, cur_N, d_h], k_selected: [B, cur_N, top_k*bs, d_h]
            # Broadcasting: g heads share the same KV
            # [B, g, cur_N, 1, d_h] @ [B, 1, cur_N, d_h, top_k*bs] -> [B, g, cur_N, 1, top_k*bs]
            scores = torch.matmul(q_chunk.unsqueeze(3), 
                                  k_selected.unsqueeze(1).transpose(-1, -2)).squeeze(3)
            scores = scores * sm_scale

            # 6. Apply Mask
            # Causal Mask: j <= i (t_idx is global j, i is i_start + arange(cur_N))
            i_global = torch.arange(i_start, i_end, device=device).view(1, 1, cur_N, 1)
            mask_causal = (t_idx.unsqueeze(1) > i_global) # [B, 1, cur_N, top_k*bs]
            
            # Combine pad mask (-1) and causal mask
            scores.masked_fill_(mask_invalid.unsqueeze(1) | mask_causal, float('-inf'))

            # 7. Softmax & Aggregation
            probs = torch.softmax(scores, dim=-1).unsqueeze(3) # [B, g, cur_N, 1, top_k*bs]
            # [B, g, cur_N, 1, top_k*bs] @ [B, 1, cur_N, top_k*bs, d_h] -> [B, g, cur_N, 1, d_h]
            chunk_out = torch.matmul(probs, v_selected.unsqueeze(1)).squeeze(3)
            
            # Write back
            out[:, hk_idx*g : (hk_idx+1)*g, i_start:i_end, :] = chunk_out.to(out.dtype)

    return out
