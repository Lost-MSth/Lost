from typing import Dict

import kdt
import torch

# =============================================================================
# Task 1: Vector add (single-job, software-pipelined ring buffer)
# =============================================================================


def _task1_num_jobs(task_args: Dict[str, int]) -> int:
    # One SM; single job avoids per-job overhead.
    return 1


@kdt.kernel(num_jobs_calculator=_task1_num_jobs)
def task1_vector_add(task_args: Dict[str, int], io_tensors: Dict[str, kdt.Tile]):
    N = task_args['N']

    SEG = 1024               # segment length
    SLOTS = 8                # ring buffer slots
    PREFETCH = SLOTS - 1     # prefetch distance
    BUF = SEG * SLOTS

    # Ring buffers on SPM
    a_buf = kdt.alloc_spm((BUF,), dtype='float32')
    b_buf = kdt.alloc_spm((BUF,), dtype='float32')
    c_buf = kdt.alloc_spm((BUF,), dtype='float32')

    total_seg = N // SEG

    # Warmup: load first PREFETCH segments so that segment i is present
    # before it is first used.
    for j in range(PREFETCH):
        slot = j % SLOTS
        s0 = slot * SEG
        s1 = s0 + SEG
        g0 = j * SEG
        g1 = g0 + SEG
        kdt.load(io_tensors['a'][g0:g1], a_buf[s0:s1])
        kdt.load(io_tensors['b'][g0:g1], b_buf[s0:s1])

    # Main pipelined loop.
    for i in range(total_seg):
        cur_slot = i % SLOTS
        s0 = cur_slot * SEG
        s1 = s0 + SEG
        g0 = i * SEG
        g1 = g0 + SEG

        # Compute current segment.
        kdt.add(a_buf[s0:s1], b_buf[s0:s1], c_buf[s0:s1])

        # Prefetch a future segment into its slot while VXM is working.
        nxt = i + PREFETCH
        if nxt < total_seg:
            nxt_slot = nxt % SLOTS
            t0 = nxt_slot * SEG
            t1 = t0 + SEG
            h0 = nxt * SEG
            h1 = h0 + SEG
            kdt.load(io_tensors['a'][h0:h1], a_buf[t0:t1])
            kdt.load(io_tensors['b'][h0:h1], b_buf[t0:t1])

        # Store current segment.
        kdt.store(c_buf[s0:s1], io_tensors['c'][g0:g1])


# =============================================================================
# Task 2: Matmul C = A @ B (128x128 tiles, K chunk 128, ping-pong A/B buffers)
# =============================================================================

def _task2_num_jobs(task_args: Dict[str, int]) -> int:
    M = task_args['M']
    N = task_args['N']
    BM = 128
    BN = 128
    return (M // BM) * (N // BN)


@kdt.kernel(num_jobs_calculator=_task2_num_jobs)
def task2_matmul(task_args: Dict[str, int], io_tensors: Dict[str, kdt.Tile]):
    M = task_args['M']
    N = task_args['N']
    K = task_args['K']

    BM = 128
    BN = 128
    BK = 128

    job_id = kdt.get_job_id()
    n_tiles = N // BN
    m_tile = job_id // n_tiles
    n_tile = job_id - m_tile * n_tiles

    m0 = m_tile * BM
    n0 = n_tile * BN

    # Buffers
    A0 = kdt.alloc_spm((BM, BK), dtype='float32')
    A1 = kdt.alloc_spm((BM, BK), dtype='float32')
    B0 = kdt.alloc_spm((BK, BN), dtype='float32')
    B1 = kdt.alloc_spm((BK, BN), dtype='float32')
    C = kdt.alloc_spm((BM, BN), dtype='float32', init_value=0.0)

    num_k = K // BK

    # Initial load for k=0 into buf0
    kdt.load(io_tensors['A'][m0:m0+BM, 0:BK], A0)
    kdt.load(io_tensors['B'][0:BK, n0:n0+BN], B0)

    for k_idx in range(num_k):
        cur0 = (k_idx % 2) == 0
        if cur0:
            Acur = A0
            Bcur = B0
            Anxt = A1
            Bnxt = B1
            # Prefetch next K chunk as early as possible.
            if k_idx + 1 < num_k:
                k1 = (k_idx + 1) * BK
                kdt.load(io_tensors['A'][m0:m0+BM, k1:k1+BK], Anxt)
                kdt.load(io_tensors['B'][k1:k1+BK, n0:n0+BN], Bnxt)

            # Accumulate.
            kdt.matmul(Acur, Bcur, C, accumulate=True)
        else:
            Acur = A1
            Bcur = B1
            Anxt = A0
            Bnxt = B0
            # Prefetch next K chunk as early as possible.
            if k_idx + 1 < num_k:
                k1 = (k_idx + 1) * BK
                kdt.load(io_tensors['A'][m0:m0+BM, k1:k1+BK], Anxt)
                kdt.load(io_tensors['B'][k1:k1+BK, n0:n0+BN], Bnxt)

            # Accumulate.
            kdt.matmul(Acur, Bcur, C, accumulate=True)

    # Store result
    kdt.store(C, io_tensors['C'][m0:m0+BM, n0:n0+BN])


# =============================================================================
# Task 3: Matmul with fine-grain scale
# =============================================================================

def _task3_num_jobs(task_args: Dict[str, int]) -> int:
    M = task_args["M"]
    N = task_args["N"]
    BM = 128
    BN = 128
    return (M // BM) * (N // BN)


@kdt.kernel(num_jobs_calculator=_task3_num_jobs)
def task3_matmul_fine_scale(task_args: Dict[str, int], io_tensors: Dict[str, kdt.Tile]):
    M = task_args["M"]
    N = task_args["N"]
    K = task_args["K"]

    BM = 128
    BN = 128
    BK = 256
    SUBK = 64
    GROUPS = 4
    num_k = K // BK  # tests: 10 or 12

    job_id = kdt.get_job_id()
    grid_n = N // BN
    bm = job_id // grid_n
    bn = job_id - bm * grid_n

    m0 = bm * BM
    n0 = bn * BN
    m1 = m0 + BM
    n1 = n0 + BN

    # Ab + scales double-buffer
    Ab_buf = kdt.alloc_spm((2, BM, BK), dtype="float32")
    As_buf = kdt.alloc_spm((2, BM, GROUPS), dtype="float32")
    Bs_buf = kdt.alloc_spm((2, GROUPS, BN), dtype="float32")

    # Bb: one 256x128 working buffer (low in [0:128], high in [128:256])
    Bb_buf = kdt.alloc_spm((BK, BN), dtype="float32")

    # Bb_hi_alt: used ONLY as staging buffer for next block LOW half (128x128),
    # we no longer use it to store current high.
    Bb_hi_alt = kdt.alloc_spm((128, BN), dtype="float32")

    C = kdt.alloc_spm((BM, BN), dtype="float32", init_value=0.0)

    # -------------------------
    # Prologue: load block0 Ab, Bb(low+high), As/Bs
    # -------------------------
    kdt.load(io_tensors["Ab"][m0:m1, 0:BK], Ab_buf[0])
    kdt.load(io_tensors["Bb"][0:128, n0:n1], Bb_buf[0:128, :])
    kdt.load(io_tensors["Bb"][128:256, n0:n1], Bb_buf[128:256, :])
    kdt.load(io_tensors["As"][m0:m1, 0:GROUPS], As_buf[0])
    kdt.load(io_tensors["Bs"][0:GROUPS, n0:n1], Bs_buf[0])

    # pre-scale group0 of block0 once
    Ab0 = Ab_buf[0][:, 0:SUBK]
    As0 = As_buf[0][:, 0:1]
    As0b = kdt.broadcast_to(As0, dim=1, new_size=SUBK)
    kdt.mul(Ab0, As0b, out=Ab0)

    Bb0 = Bb_buf[0:SUBK, :]
    Bs0 = Bs_buf[0][0:1, :]
    Bs0b = kdt.broadcast_to(Bs0, dim=0, new_size=SUBK)
    kdt.mul(Bb0, Bs0b, out=Bb0)

    # -------------------------
    # Main loop
    # Invariant: at loop entry, current block low is in Bb_buf[0:128],
    #            current block high will be loaded into Bb_buf[128:256] (except kb=0 already loaded),
    #            current block group0 already scaled.
    # -------------------------
    for kb in range(num_k):
        p = kb % 2
        q = 1 - p

        k_base = kb * BK
        s_base = kb * GROUPS
        has_next = (kb + 1) < num_k

        # ---- for kb>0: load CURRENT high half early (no hazard with low) ----
        if kb > 0:
            kdt.load(
                io_tensors["Bb"][k_base + 128:k_base + 256, n0:n1],
                Bb_buf[128:256, :],
            )

        # ---- g0 MXM (already scaled) ----
        if kb == 0:
            kdt.matmul(Ab_buf[p][:, 0:SUBK],
                       Bb_buf[0:SUBK, :], out=C, accumulate=False)
        else:
            kdt.matmul(Ab_buf[p][:, 0:SUBK],
                       Bb_buf[0:SUBK, :], out=C, accumulate=True)

        # ---- prefetch NEXT Ab/As/Bs and stage NEXT low-half into Bb_hi_alt ASAP ----
        if has_next:
            nk_base = (kb + 1) * BK
            ns_base = (kb + 1) * GROUPS

            kdt.load(io_tensors["Ab"][m0:m1, nk_base:nk_base + BK], Ab_buf[q])
            kdt.load(io_tensors["As"]
                     [m0:m1, ns_base:ns_base + GROUPS], As_buf[q])
            kdt.load(io_tensors["Bs"]
                     [ns_base:ns_base + GROUPS, n0:n1], Bs_buf[q])

            # Stage next low half into Bb_hi_alt (no hazard; independent buffer)
            kdt.load(io_tensors["Bb"][nk_base:nk_base + 128, n0:n1], Bb_hi_alt)

        # ---- g1 scale+MXM (low 64:128) ----
        Ab1 = Ab_buf[p][:, SUBK:2*SUBK]
        As1 = As_buf[p][:, 1:2]
        As1b = kdt.broadcast_to(As1, dim=1, new_size=SUBK)
        kdt.mul(Ab1, As1b, out=Ab1)

        Bb1 = Bb_buf[SUBK:2*SUBK, :]
        Bs1 = Bs_buf[p][1:2, :]
        Bs1b = kdt.broadcast_to(Bs1, dim=0, new_size=SUBK)
        kdt.mul(Bb1, Bs1b, out=Bb1)

        kdt.matmul(Ab1, Bb1, out=C, accumulate=True)

        # ---- g2 scale+MXM (high 128:192) ----
        Ab2 = Ab_buf[p][:, 2*SUBK:3*SUBK]
        As2 = As_buf[p][:, 2:3]
        As2b = kdt.broadcast_to(As2, dim=1, new_size=SUBK)
        kdt.mul(Ab2, As2b, out=Ab2)

        Bb2 = Bb_buf[128:128+SUBK, :]
        Bs2 = Bs_buf[p][2:3, :]
        Bs2b = kdt.broadcast_to(Bs2, dim=0, new_size=SUBK)
        kdt.mul(Bb2, Bs2b, out=Bb2)

        kdt.matmul(Ab2, Bb2, out=C, accumulate=True)

        # ---- during g2/g3 window: copy staged NEXT low -> Bb_buf[0:128] ----
        # This replaces the boundary DMA stall with an on-chip copy (cheap, hideable).
        if has_next:
            kdt.copy(Bb_hi_alt, Bb_buf[0:128, :])

        # ---- g3 scale+MXM (high 192:256) ----
        Ab3 = Ab_buf[p][:, 3*SUBK:4*SUBK]
        As3 = As_buf[p][:, 3:4]
        As3b = kdt.broadcast_to(As3, dim=1, new_size=SUBK)
        kdt.mul(Ab3, As3b, out=Ab3)

        Bb3 = Bb_buf[192:256, :]
        Bs3 = Bs_buf[p][3:4, :]
        Bs3b = kdt.broadcast_to(Bs3, dim=0, new_size=SUBK)
        kdt.mul(Bb3, Bs3b, out=Bb3)

        kdt.matmul(Ab3, Bb3, out=C, accumulate=True)

        # ---- pre-scale NEXT block group0 at end (so next iter launches g0 immediately) ----
        if has_next:
            Abn0 = Ab_buf[q][:, 0:SUBK]
            Asn0 = As_buf[q][:, 0:1]
            Asn0b = kdt.broadcast_to(Asn0, dim=1, new_size=SUBK)
            kdt.mul(Abn0, Asn0b, out=Abn0)

            Bbn0 = Bb_buf[0:SUBK, :]
            Bsn0 = Bs_buf[q][0:1, :]
            Bsn0b = kdt.broadcast_to(Bsn0, dim=0, new_size=SUBK)
            kdt.mul(Bbn0, Bsn0b, out=Bbn0)

    kdt.store(C, io_tensors["C"][m0:m1, n0:n1])


# =============================================================================
# Task 4: Flash Attention (blockwise online softmax)
# =============================================================================


def _task4_num_jobs(task_args: Dict[str, int]) -> int:
    S_qo = task_args["S_qo"]
    BR = 128
    return S_qo // BR


@kdt.kernel(num_jobs_calculator=_task4_num_jobs)
def task4_flash_attention(task_args: Dict[str, int], io_tensors: Dict[str, kdt.Tile]):
    S_qo = task_args["S_qo"]
    S_kv = task_args["S_kv"]
    D = task_args["D"]

    BR = 128
    BC = 128

    job_id = kdt.get_job_id()
    q0 = job_id * BR
    q1 = q0 + BR

    num_kv_blocks = S_kv // BC

    # Buffers
    Q = kdt.alloc_spm((BR, D), dtype="float32")
    K_buf = kdt.alloc_spm((2, BC, D), dtype="float32")
    V_buf = kdt.alloc_spm((2, BC, D), dtype="float32")

    # Double buffer S to allow overlapping QK^T of next block with SV of current block
    S_buf = kdt.alloc_spm((2, BR, BC), dtype="float32")

    # Accumulators and temporary
    tmp_O = kdt.alloc_spm((BR, D), dtype="float32")
    m = kdt.alloc_spm((BR,), dtype="float32")
    l = kdt.alloc_spm((BR,), dtype="float32")
    Oacc = kdt.alloc_spm((BR, D), dtype="float32")

    rowmax = kdt.alloc_spm((BR,), dtype="float32")
    m_new = kdt.alloc_spm((BR,), dtype="float32")
    alpha = kdt.alloc_spm((BR,), dtype="float32")
    sumP = kdt.alloc_spm((BR,), dtype="float32")

    # Init
    kdt.load(io_tensors["Q"][q0:q1, :], Q)
    kdt.fill(m, -1.0e9)
    kdt.fill(l, 0.0)
    kdt.fill(Oacc, 0.0)

    # Prologue: Load KV[0] and compute S[0]
    kdt.load(io_tensors["K"][0:BC, :], K_buf[0])
    kdt.load(io_tensors["V"][0:BC, :], V_buf[0])

    Kt = kdt.transpose(K_buf[0], 0, 1)
    kdt.matmul(Q, Kt, out=S_buf[0], accumulate=False)

    E = 2.7182818284590451

    for b in range(num_kv_blocks):
        p = b % 2
        q = 1 - p

        # --- Prefetch and Pipelined MXM ---
        # If there is a next block (b+1):
        # 1. Start loading K[q], V[q] (Async Load)
        # 2. Issue Matmul Q @ K[q]^T -> S[q] (Async MXM)
        #    This MXM will queue behind the current work but doesn't depend on VXM of block b.
        #    This fills the MXM pipeline bubble that would otherwise exist during VXM.
        if b + 1 < num_kv_blocks:
            k_nxt = (b + 1) * BC
            kdt.load(io_tensors["K"][k_nxt:k_nxt+BC, :], K_buf[q])
            kdt.load(io_tensors["V"][k_nxt:k_nxt+BC, :], V_buf[q])

            Kt_next = kdt.transpose(K_buf[q], 0, 1)
            kdt.matmul(Q, Kt_next, out=S_buf[q], accumulate=False)

        # --- VXM Part (Softmax Logic) for block b ---
        # All these VXM ops run in parallel with the MXM of (b+1) issued above
        S_curr = S_buf[p]

        # rowmax = max(S_curr)
        kdt.reduce(S_curr, dim=1, op="max", out=rowmax)

        # m_new = max(m, rowmax)
        kdt.max(m, rowmax, out=m_new)

        # alpha = exp(m - m_new)
        kdt.sub(m, m_new, out=alpha)
        kdt.exp(alpha, out=alpha, y=E)

        # Scale accumulators: Oacc *= alpha, l *= alpha
        a2 = kdt.unsqueeze(alpha, dim=1)
        a2b = kdt.broadcast_to(a2, dim=1, new_size=D)
        kdt.mul(Oacc, a2b, out=Oacc)  # VXM
        kdt.mul(l, alpha, out=l)     # VXM

        # Update m
        kdt.copy(m_new, m)

        # P = exp(S_curr - m_new)
        m2 = kdt.unsqueeze(m_new, dim=1)
        m2b = kdt.broadcast_to(m2, dim=1, new_size=BC)
        kdt.sub(S_curr, m2b, out=S_curr)
        kdt.exp(S_curr, out=S_curr, y=E)

        # l += sum(P)
        kdt.reduce(S_curr, dim=1, op="sum", out=sumP)
        kdt.add(l, sumP, out=l)

        # --- MXM Part (Value Aggregation) for block b ---
        # Oacc += S_curr @ V_curr
        # This depends on Oacc scaling and S_curr calc (both VXM).
        # It will execute after VXM is done.
        # If Q@K_next was issued, this runs after it, keeping MXM 100% busy.
        kdt.matmul(S_curr, V_buf[p], out=Oacc, accumulate=True)

    # Epilogue: O = Oacc / l
    l2 = kdt.unsqueeze(l, dim=1)
    l2b = kdt.broadcast_to(l2, dim=1, new_size=D)
    kdt.div(Oacc, l2b, out=Oacc)

    kdt.store(Oacc, io_tensors["O"][q0:q1, :])


def get_kernel(task_id: int) -> kdt.KernelFunction:
    if task_id == 1:
        return task1_vector_add
    elif task_id == 2:
        return task2_matmul
    elif task_id == 3:
        return task3_matmul_fine_scale
    elif task_id == 4:
        return task4_flash_attention
    else:
        raise ValueError(f"未知的 task_id: {task_id}")
