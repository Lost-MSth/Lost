import torch
import kdt

import lib

def test_task4(testcase_id: int, players_kernel: kdt.KernelFunction, print_ir: bool) -> float:
    lib.set_random_seed(0)

    S_qo, S_kv, D, T = [
        (1024, 128, 128, 8000),
        (1024, 2048, 128, 36408),
        (1024, 4096, 128, 71234),
        (2048, 4096, 128, 142469),
    ][testcase_id]

    task_args = {
        'S_qo': S_qo,
        'S_kv': S_kv,
        'D': D
    }
    tpu_spec = kdt.TPUSpec(num_sms=8, load_store_latency=1000, spm_size=640*1024)
    players_kernel_handler = lib.PlayersKernelHandler(
        players_kernel,
        task_args,
        tpu_spec,
        print_ir
    )

    num_cycles = None
    for _ in range(3):
        Q = (torch.randn((S_qo, D), dtype=torch.float32)/10).clamp(-1, +1)
        K = (torch.randn((S_kv, D), dtype=torch.float32)/10).clamp(-1, +1)
        V = (torch.randn((S_kv, D), dtype=torch.float32)/10).clamp(-1, +1)
        O = torch.empty_like(Q)

        num_cycles = players_kernel_handler.run({
            'Q': Q,
            'K': K,
            'V': V,
            'O': O
        })
        if num_cycles == float('inf'):
            print("Simulation timeout")
            return 0
        
        attn_score = torch.softmax(Q @ K.transpose(0, 1), dim=-1)
        O_ref = attn_score @ V
        if not kdt.utils.check_is_allclose("task1_output", O, O_ref, abs_tol=1e-5, rel_tol=2e-3):
            print("Incorrect result")
            return 0

    score = lib.calculate_score(num_cycles, T, is_correct=True)
    mfu = ((S_qo*S_kv*(D+D))/num_cycles) / (2048*tpu_spec.num_sms)
    print(f"Testcase {testcase_id} passed, num_cycles: {num_cycles} ({mfu*100:.1f}% of MXM's peak), score: {score:.1f}")

    return score
