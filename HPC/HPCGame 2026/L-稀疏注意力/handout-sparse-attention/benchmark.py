import torch
import argparse
import sys
import time
import math

try:
    import triton
    from triton.testing import do_bench
except ImportError:
    print("Triton is not installed. Benchmarking might be less accurate.")
    def do_bench(fn, warmup=25, rep=100):
        for _ in range(warmup):
            fn()
        torch.cuda.synchronize()
        start = time.time()
        for _ in range(rep):
            fn()
        torch.cuda.synchronize()
        end = time.time()
        return (end - start) / rep * 1000

from ref import reference_sparse_attention
try:
    from solution import sparse_attention
except ImportError:
    print("Could not import 'solution.py'. Make sure your solution is implemented in 'solution.py' with a function 'sparse_attention'.")
    sys.exit(1)

def get_problem_size(set_name):
    # (B, H_Q, H_K, N, M, D_H, TOP_K, BS)
    if set_name == "small":
        return [(1, 16, 1, 128, 128, 64, 4, 64)]
    elif set_name == "medium":
        return [(1, 64, 4, 1024, 1024, 64, 16, 64)]
    elif set_name == "large":
        return [
            # B, H_Q, H_K, N, M, D_H, TOP_K, BS
            (1, 64, 4, 4096, 4096, 128, 32, 64),
            (2, 64, 4, 8192, 8192, 128, 64, 64),
        ]
    elif set_name == "all":
         return get_problem_size("small") + get_problem_size("medium") + get_problem_size("large")
    else:
        raise ValueError(f"Unknown problem set: {set_name}")

def prepare_data(B, H_Q, H_K, N, M, D_H, TOP_K, BS, device="cuda"):
    dtype = torch.float16
    q = torch.randn((B, H_Q, N, D_H), device=device, dtype=dtype)
    k = torch.randn((B, H_K, M, D_H), device=device, dtype=dtype)
    v = torch.randn((B, H_K, M, D_H), device=device, dtype=dtype)
    
    # Generate legal sparse index (Causal-aware: index can only point to current or previous blocks)
    index = torch.zeros((B, H_K, N, TOP_K), device=device, dtype=torch.int32)
    
    max_blocks = (M + BS - 1) // BS

    for i in range(N):
        max_block_id = min(i // BS, max_blocks - 1)
        possible_ids = torch.arange(0, max_block_id + 1, device=device)
        
        if len(possible_ids) <= TOP_K:
            selection = torch.cat([possible_ids, torch.full((TOP_K - len(possible_ids),), -1, device=device)])
        else:
            perm = torch.randperm(len(possible_ids), device=device)[:TOP_K]
            selection = possible_ids[perm]
            
        index[:, :, i, :] = selection.to(torch.int32)
        
    return q, k, v, index

def run_benchmark(args):
    device = torch.device("cuda")
    problems = get_problem_size(args.size)
    
    print(f"{'Size (B, H_Q, H_K, N, M, D, K, BS)':<40} | {'Status':<10} | {'Latency (ms)':<15} | {'TFLOPS':<10}")
    print("-" * 85)

    for p in problems:
        B, H_Q, H_K, N, M, D_H, TOP_K, BS = p
        sm_scale = 1.0 / (D_H ** 0.5)
        
        try:
            print(f"Preparing data for {p}...")
            q, k, v, index = prepare_data(B, H_Q, H_K, N, M, D_H, TOP_K, BS, device)
        except Exception as e:
            print(f"Error preparing data for {p}: {e}")
            continue

        # Correctness Check
        try:
            if args.check:
                # Run Ref
                out_ref = reference_sparse_attention(q, k, v, index, BS, sm_scale)
                # Run Sol
                out_sol = sparse_attention(q, k, v, index, BS, sm_scale)
                
                # Check
                torch.testing.assert_close(out_sol, out_ref, atol=1e-2, rtol=1e-2)
                status = "PASS"
            else:
                status = "N/A"
        except AssertionError as e:
            status = "FAIL"
            # print(e)
        except Exception as e:
            status = f"ERR: {e}"
            print(e)
        
        # Performance
        if status == "PASS" or not args.check:
            fn = lambda: sparse_attention(q, k, v, index, BS, sm_scale)
            ms = do_bench(fn, warmup=10, rep=50)
            
            # Flops: 2 * (QK_dot + PV_dot) * occurrences
            # Simplification: B * H_Q * N * TOP_K * BS * D_H * 4
            flops = 4 * B * H_Q * N * TOP_K * BS * D_H
            tflops = (flops / 1e12) / (ms / 1e3)
        else:
            ms = 0
            tflops = 0

        p_str = str(p)
        print(f"{p_str:<40} | {status:<10} | {ms:<15.3f} | {tflops:<10.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=str, default="small", choices=["small", "medium", "large", "all"], help="Problem size set")
    parser.add_argument("--check", action="store_true", default=True, help="Run correctness check")
    parser.add_argument("--no-check", dest="check", action="store_false", help="Skip correctness check")
    args = parser.parse_args()
    
    run_benchmark(args)
