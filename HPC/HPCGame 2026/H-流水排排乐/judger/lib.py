from typing import Dict

import random
import numpy as np
import torch

import kdt

def set_random_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

class PlayersKernelHandler:
    def __init__(self, players_kernel: kdt.KernelFunction, task_args: Dict[str, int], tpu_spec: kdt.TPUSpec, print_ir: bool):
        self.players_kernel = players_kernel
        self.compiled_kernel = None
        self.tpu_spec = tpu_spec
        self.task_args = task_args
        self.print_ir = print_ir

    def run(self, io_tensors: Dict[str, torch.Tensor]) -> int:
        if self.compiled_kernel is None:
            self.compiled_kernel = self.players_kernel.compile(self.task_args, io_tensors)
            if self.print_ir:
                self.compiled_kernel.print_ir()
        try:
            num_cycles = kdt.launch_kernel(self.compiled_kernel, io_tensors, self.tpu_spec)
        except TimeoutError:
            num_cycles = float('inf')  # Indicate timeout with infinite cycles
        return num_cycles

def calculate_score(num_cycles: int, num_cycles_thres: int, is_correct: bool = True) -> float:
    """
    Calculate the score based on the number of cycles taken by the player's kernel.
    The returned score lies between 0 and 100.
    """
    if not is_correct:
        return 0.0
    if num_cycles <= num_cycles_thres:
        return 100.0
    else:
        score = 10 + (num_cycles_thres / num_cycles)**4 * 90.0
        return score
    