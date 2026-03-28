import torch
import triton
import triton.language as tl

@triton.autotune(
    configs=[
        triton.Config({'num_warps': 8, 'num_stages': 3}, num_warps=8),
        triton.Config({'num_warps': 8, 'num_stages': 4}, num_warps=8),
        triton.Config({'num_warps': 4, 'num_stages': 4}, num_warps=4),
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
    pid_n = tl.program_id(0)
    pid_hk = tl.program_id(1)
    pid_b = tl.program_id(2)

    # 偏移量预设
    offs_g = tl.arange(0, BLOCK_G)
    offs_d = tl.arange(0, BLOCK_D)
    offs_bs = tl.arange(0, BLOCK_BS)

    # 加载 Q 向量 [G, D_H]
    q_base = Q + pid_b * stride_qb + (pid_hk * G) * stride_qh + pid_n * stride_qn
    q_ptrs = q_base + offs_g[:, None] * stride_qh + offs_d[None, :] * stride_qd
    q = tl.load(q_ptrs, mask=(offs_g[:, None] < G), other=0.0).to(tl.float16)
    q = (q * sm_scale).to(tl.float16)

    # Index 指针
    idx_ptr = Index + pid_b * stride_ib + pid_hk * stride_ih + pid_n * stride_in
    
    # 累加器 (FP32)
    m_i = tl.full([BLOCK_G], -float('inf'), dtype=tl.float32)
    l_i = tl.zeros([BLOCK_G], dtype=tl.float32)
    acc = tl.zeros([BLOCK_G, BLOCK_D], dtype=tl.float32)

    cur_query_block_idx = pid_n // BS
    
    # 提前计算 K/V 的固定偏移
    k_base = K + pid_b * stride_kb + pid_hk * stride_kh
    v_base = V + pid_b * stride_vb + pid_hk * stride_vh
    
    # 预计算块跨度
    bs_stride_km = BS * stride_km
    bs_stride_vm = BS * stride_vm

    # TOP_K 循环
    for tk in range(TOP_K):
        # 向量化加载 Index
        block_idx = tl.load(idx_ptr + tk * stride_ik)
        
        if block_idx >= 0:
            start_m = block_idx * BS
            
            # 加载 K block [BS, D_H]
            # 使用 tl.multiple_of 提示编译器对齐，加速 LDG
            offs_k = block_idx * bs_stride_km + offs_bs[:, None] * stride_km + offs_d[None, :] * stride_kd
            k = tl.load(k_base + offs_k, mask=((start_m + offs_bs[:, None]) < M), other=0.0).to(tl.float16)

            # 点积 QK^T
            qk = tl.dot(q, tl.trans(k))

            # 掩码优化
            if block_idx >= cur_query_block_idx:
                mask = (start_m + offs_bs[None, :]) <= pid_n
                qk = tl.where(mask, qk, -float('inf'))

            # 在线 Softmax 更新
            m_ij = tl.max(qk, axis=1)
            m_next = tl.maximum(m_i, m_ij)
            
            p = tl.exp(qk - m_next[:, None])
            alpha = tl.exp(m_i - m_next)
            
            # 更新 denominator
            l_i = l_i * alpha + tl.sum(p, axis=1)

            # 加载 V block [BS, D_H] 并更新 accumulator
            offs_v = block_idx * bs_stride_vm + offs_bs[:, None] * stride_vm + offs_d[None, :] * stride_vd
            v = tl.load(v_base + offs_v, mask=((start_m + offs_bs[:, None]) < M), other=0.0).to(tl.float16)
            
            acc = acc * alpha[:, None] + tl.dot(p.to(tl.float16), v)
            m_i = m_next

    # 最终归一化
    acc = acc / (l_i[:, None] + 1e-10)
    
    # 存储结果
    out_base = Out + pid_b * stride_ob + (pid_hk * G) * stride_oh + pid_n * stride_on
    out_ptrs = out_base + offs_g[:, None] * stride_oh + offs_d[None, :] * stride_od
    tl.store(out_ptrs, acc.to(tl.float16), mask=(offs_g[:, None] < G))

def sparse_attention(q, k, v, index, block_size, sm_scale):
    B, H_Q, N, D_H = q.shape
    _, H_K, M, _ = k.shape
    _, _, _, top_K = index.shape
    
    G = H_Q // H_K
    out = torch.empty_like(q)
    
    # 对齐策略
    BLOCK_D = D_H
    BLOCK_BS = block_size
    # 强制 BLOCK_G 至少为 16 且为 2 的幂以优化 Tensor Core
    BLOCK_G = 16 if G <= 16 else (1 << (G - 1).bit_length())

    # 每个线程块处理一个 Query Token 和对应的所有 G 个头
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