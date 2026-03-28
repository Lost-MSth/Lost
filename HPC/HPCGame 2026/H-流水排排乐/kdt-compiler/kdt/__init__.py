"""
KDT-DSL: A Domain-Specific Language for Kernel Design Trial.

This package provides the KDT-DSL compiler and runtime for the
Peking University HPCGame 2026 competition.
"""
from typing import Tuple, Union
from functools import wraps

# Re-export public API from language module
from kdt.language import kernel, launch_kernel, KernelFunction, CompiledKernel
from kdt.ir import Tile
from kdt import utils
from kdt.simulator import TPUSpec
import kdt

# ----------------------------------------------------------------------
# KDT-DSL instruction stubs
# These functions raise errors when called outside of a @kdt.kernel function.
# Inside a kernel, they are recognized by the AST visitor and transformed
# into corresponding IR instructions.
# ----------------------------------------------------------------------

def _raise_outside_kernel(instr_name: str):
    """Raise error for KDT-DSL instruction called outside kernel."""
    from kdt.language.errors import SemanticError
    raise SemanticError(
        f"kdt.{instr_name} can only be called inside a @kdt.kernel function"
    )

from typing import TYPE_CHECKING
_empty_tile = Tile(None, None) if TYPE_CHECKING else None   # type: ignore

# Memory allocation
def alloc_spm(shape: Tuple[int, ...], dtype: str="float32", name: str="", init_value: Union[str, int, bool]=0) -> Tile:
    _raise_outside_kernel("alloc_spm")
    return _empty_tile

# Metadata
def get_job_id() -> int:
    _raise_outside_kernel("get_job_id")
    return -1

# Shape transformation
def squeeze(x: Tile, dim: int) -> Tile:
    _raise_outside_kernel("squeeze")
    return _empty_tile

def unsqueeze(x: Tile, dim: int) -> Tile:
    _raise_outside_kernel("unsqueeze")
    return _empty_tile

def broadcast_to(x: Tile, dim: int, new_size: int) -> Tile:
    _raise_outside_kernel("broadcast_to")
    return _empty_tile

def transpose(x: Tile, dim1: int, dim2: int) -> Tile:
    _raise_outside_kernel("transpose")
    return _empty_tile

def slice(x: Tile, dim: int, start: int, end: int) -> Tile:
    _raise_outside_kernel("slice")
    return _empty_tile

# Computation
def exp(x: Tile, out: Tile, y: float):
    _raise_outside_kernel("exp")

def log(x: Tile, out: Tile, y: float):
    _raise_outside_kernel("log")

def pow(x: Tile, out: Tile, y: float):
    _raise_outside_kernel("pow")

def add(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("add")

def sub(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("sub")

def mul(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("mul")

def div(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("div")

def max(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("max")

def min(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("min")

def logical_and(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("logical_and")

def logical_or(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("logical_or")

def le(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("le")

def leq(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("leq")

def eq(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("eq")

def neq(a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("neq")

def fma(a: Tile, b: Tile, c: Tile, out: Tile):
    _raise_outside_kernel("fma")

def matmul(a: Tile, b: Tile, out: Tile, accumulate: bool = False):
    _raise_outside_kernel("matmul")

def reduce(x: Tile, dim: int, op: str, out: Tile):
    _raise_outside_kernel("reduce")

# Selection
def where(cond: Tile, a: Tile, b: Tile, out: Tile):
    _raise_outside_kernel("where")

def copy(x: Tile, y: Tile):
    _raise_outside_kernel("copy")

def fill(x: Tile, value: float):
    _raise_outside_kernel("fill")

# Data transportation
def load(src: Tile, dst: Tile):
    _raise_outside_kernel("load")

def store(src: Tile, dst: Tile):
    _raise_outside_kernel("store")

# Debugging
def print(x: Tile, msg: str = "", print_only_if_job0: bool = False):
    _raise_outside_kernel("print")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

__all__ = [
    # Decorator and launch
    'kernel',
    'launch_kernel',
    # Memory allocation
    'alloc_spm',
    # Meta operations
    'get_job_id',
    # Shape operations
    'broadcast_to',
    'slice',
    'transpose',
    # Computation
    'exp',
    'log',
    'pow',
    'add',
    'sub',
    'mul',
    'div',
    'max',
    'min',
    'logical_and',
    'logical_or',
    'le',
    'leq',
    'eq',
    'neq',
    'matmul',
    'fma',
    'reduce',
    # Selection
    'where',
    'fill',
    # Data movement
    'load',
    'store',
    # Debugging
    'print',
]