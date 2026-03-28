import torch

if hasattr(torch, 'npu') and torch.npu.is_available():
    def sparse_attention(q, k, v, index, bs, sm_scale):
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


else:

    import triton
    import triton.language as tl

    @triton.autotune(
        configs=[
            # 针对 D_H=128 的大模型推理场景，8 warps 配合 2-3 stages 通常能获得最高的 Occupancy
            triton.Config({'num_warps': 8, 'num_stages': 2}),
            triton.Config({'num_warps': 8, 'num_stages': 3}),
            triton.Config({'num_warps': 4, 'num_stages': 2}),
        ],
        key=["D_H", "BS", "G", "TOP_K"],
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
        # 程序索引
        pid_n = tl.program_id(0)
        pid_hk = tl.program_id(1)
        pid_b = tl.program_id(2)

        # 偏移量
        offs_g = tl.arange(0, BLOCK_G)
        offs_d = tl.arange(0, BLOCK_D)
        offs_bs = tl.arange(0, BLOCK_BS)

        # 加载 Q: [BLOCK_G, BLOCK_D] (预缩放以减少循环内指令)
        q_base = Q + pid_b * stride_qb + (pid_hk * G) * stride_qh + pid_n * stride_qn
        q_ptrs = q_base + (offs_g[:, None] * stride_qh + offs_d[None, :] * stride_qd)
        # Mask 处理 GQA 组数（通常 G=16）
        q = tl.load(q_ptrs, mask=(offs_g[:, None] < G), other=0.0)
        q = (q * sm_scale).to(tl.float16)

        # Index 指针
        idx_ptr = Index + pid_b * stride_ib + pid_hk * stride_ih + pid_n * stride_in
        
        # 初始化在线 Softmax
        m_i = tl.full([BLOCK_G], -float('inf'), dtype=tl.float32)
        l_i = tl.zeros([BLOCK_G], dtype=tl.float32)
        acc = tl.zeros([BLOCK_G, BLOCK_D], dtype=tl.float32)

        # KV 基址偏移
        kv_head_off = pid_b * stride_kb + pid_hk * stride_kh
        v_head_off = pid_b * stride_vb + pid_hk * stride_vh
        
        # 核心循环
        for tk in range(0, TOP_K):
            # 加载块索引 (int32)
            block_idx = tl.load(idx_ptr + tk * stride_ik)
            
            if block_idx >= 0:
                start_m = block_idx * BS
                
                # 1. 加载 K block [BS, D_H]
                k_ptrs = K + kv_head_off + (start_m * stride_km + offs_bs[:, None] * stride_km + offs_d[None, :] * stride_kd)
                k = tl.load(k_ptrs, mask=((start_m + offs_bs[:, None]) < M), other=0.0).to(tl.float16)

                # 2. 计算点积 QK^T: [BLOCK_G, BLOCK_BS]
                qk = tl.dot(q, tl.trans(k))

                # 3. 因果遮掩优化：绝大多数历史块不需要遮掩逻辑
                if start_m + BS > pid_n:
                    mask = (start_m + offs_bs[None, :]) <= pid_n
                    qk = tl.where(mask, qk, -1.0e38)

                # 4. 加载 V block [BS, D_H]
                v_ptrs = V + v_head_off + (start_m * stride_vm + offs_bs[:, None] * stride_vm + offs_d[None, :] * stride_vd)
                v = tl.load(v_ptrs, mask=((start_m + offs_bs[:, None]) < M), other=0.0).to(tl.float16)

                # 5. 在线 Softmax 更新 (保持 FP32 精度)
                m_ij = tl.max(qk, axis=1)
                m_next = tl.maximum(m_i, m_ij)
                
                p = tl.exp(qk - m_next[:, None])
                alpha = tl.exp(m_i - m_next)
                
                l_i = l_i * alpha + tl.sum(p, axis=1)

                # 6. 更新累加器: acc = acc * alpha + dot(p, v)
                # 使用三参数 dot 直接在 Tensor Core 累加
                acc = acc * alpha[:, None]
                acc = tl.dot(p.to(tl.float16), v, acc)
                
                m_i = m_next

        # 归一化写回
        acc = acc / l_i[:, None]
        
        # 存储结果
        out_base = Out + pid_b * stride_ob + (pid_hk * G) * stride_oh + pid_n * stride_on
        out_ptrs = out_base + (offs_g[:, None] * stride_oh + offs_d[None, :] * stride_od)
        tl.store(out_ptrs, acc.to(tl.float16), mask=(offs_g[:, None] < G))

    def sparse_attention(q, k, v, index, block_size, sm_scale):
        """
        针对 D_H=128、大序列及昇腾架构深度优化的 Triton 实现。
        """
        B, H_Q, N, D_H = q.shape
        _, H_K, M, _ = k.shape
        _, _, _, top_K = index.shape
        
        # 计算 GQA 分组大小
        G = H_Q // H_K
        # 使用 q.device 确保支持 NPU/CUDA 自动切换
        out = torch.empty_like(q)
        
        # 设置 Tile 大小：BLOCK_G=16 完美匹配大模型常见的 GQA=16
        BLOCK_G = 16 
        BLOCK_D = D_H
        BLOCK_BS = block_size

        # Grid：每个 Token 作为一个独立任务，最大化并行度
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
            BLOCK_D=BLOCK_D, 
            BLOCK_BS=BLOCK_BS, 
            BLOCK_G=BLOCK_G,
        )
        
        return out