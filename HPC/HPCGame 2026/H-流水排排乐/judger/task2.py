import torch
import kdt

import lib

def test_task2(testcase_id: int, players_kernel: kdt.KernelFunction, print_ir: bool) -> float:
    lib.set_random_seed(0)

    M, N, K, T = [
        (512, 1024, 2560, 23272),
        (2048, 512, 3072, 54613)
    ][testcase_id]

    task_args = {
        'M': M,
        'N': N,
        'K': K
    }
    tpu_spec = kdt.TPUSpec(num_sms=32, load_store_latency=1000, spm_size=384*1024)
    players_kernel_handler = lib.PlayersKernelHandler(
        players_kernel,
        task_args,
        tpu_spec,
        print_ir
    )

    num_cycles = None
    for _ in range(3):
        a = (torch.randn((M, K), dtype=torch.float32) / 10).clamp(-1, 1)
        b = (torch.randn((K, N), dtype=torch.float32) / 10).clamp(-1, 1)
        c = torch.zeros((M, N), dtype=torch.float32)

        num_cycles = players_kernel_handler.run({
            'A': a,
            'B': b,
            'C': c
        })
        if num_cycles == float('inf'):
            print("Simulation timeout")
            return 0
        
        c_ref = a @ b
        if not kdt.utils.check_is_allclose("task1_output", c, c_ref, abs_tol=1e-5, rel_tol=2e-3):
            print("Incorrect result")
            return 0

    score = lib.calculate_score(num_cycles, T, is_correct=True)
    mfu = (M*N*K/num_cycles) / (2048*tpu_spec.num_sms)
    print(f"Testcase {testcase_id} passed, num_cycles: {num_cycles} ({mfu*100:.1f}% of MXM's peak), score: {score:.1f}")

    return score
