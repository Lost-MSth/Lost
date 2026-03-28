import torch
import kdt

import lib

def test_task1(testcase_id: int, players_kernel: kdt.KernelFunction, print_ir: bool) -> float:
    lib.set_random_seed(0)

    N, T = [
        (16384, 1919810),
        (64*16384, 11000)
    ][testcase_id]

    task_args = {'N': N}
    tpu_spec = kdt.TPUSpec(num_sms=1, load_store_latency=50, spm_size=128*1024)
    players_kernel_handler = lib.PlayersKernelHandler(
        players_kernel,
        task_args,
        tpu_spec,
        print_ir
    )

    num_cycles = None
    for _ in range(3):
        a = torch.randn((N,), dtype=torch.float32)
        b = torch.randn((N,), dtype=torch.float32)
        c = torch.zeros((N,), dtype=torch.float32)

        num_cycles = players_kernel_handler.run({
            'a': a,
            'b': b,
            'c': c
        })
        if num_cycles == float('inf'):
            print("Simulation timeout")
            return 0
        
        c_ref = a + b
        if not kdt.utils.check_is_allclose("task1_output", c, c_ref, abs_tol=1e-5, rel_tol=1e-5):
            print("Incorrect result")
            return 0

    score = lib.calculate_score(num_cycles, T, is_correct=True)
    print(f"Testcase {testcase_id} passed, num_cycles: {num_cycles}, score: {score:.1f}")

    return score
