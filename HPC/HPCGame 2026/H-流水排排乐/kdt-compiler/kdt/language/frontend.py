"""
Frontend decorator and compiler for KDT-DSL.
"""

import ast
import inspect
import dataclasses
from typing import Dict, Any, Callable, Optional

import torch

from kdt.ir import Kernel, TileStorage, MemorySpace, Block, DataType
from kdt.language.errors import CompilationError, SemanticError, ConstantRequiredError
from kdt.language.symbol_table import SymbolTable, SymbolInfo, VarType
from kdt.language.ast_visitor import ASTVisitor
from kdt.ir.debug import print_ir

def kernel(num_jobs_calculator: Callable):
    """
    Decorator for KDT-DSL kernel functions.

    Args:
        num_jobs_calculator: Function that takes task_args dict and returns
            number of jobs to launch.

    Returns:
        Decorated kernel function (KernelFunction instance).
    """
    def decorator(func: Callable) -> 'KernelFunction':
        return KernelFunction(func, num_jobs_calculator)
    return decorator

@dataclasses.dataclass
class IOTensorMeta:
    """
    The metadata of an input/output tensor. Recorded during compilation and checked at launch time.
    """
    dtype: DataType
    shape: tuple[int, ...]

    @staticmethod
    def from_tensor(tensor: torch.Tensor) -> 'IOTensorMeta':
        if tensor.dtype not in [torch.float32, torch.bool]:
            raise TypeError(
                f"KDT-DSL only supports torch.float32 and torch.bool tensors, got {tensor.dtype}"
            )
        dtype = {torch.float32: DataType.FLOAT32, torch.bool: DataType.BOOL}[tensor.dtype]
        return IOTensorMeta(
            dtype=dtype,
            shape=tuple(tensor.shape)
        )

class CompiledKernel:
    """
    Wrapper for a compiled kernel function.
    """
    def __init__(self, kernel_ir: Kernel, task_args: Dict[str, Any], io_tensors_meta: Dict[str, IOTensorMeta], start_lineno: int):
        self.kernel_ir = kernel_ir
        self.task_args = task_args
        self.io_tensors_meta = io_tensors_meta
        self.start_lineno = start_lineno

    def print_ir(self):
        """
        Print the IR of the compiled kernel function.
        """
        print_ir(self.kernel_ir)

    def __call__(self, *args, **kwargs):
        raise SemanticError(
            "KDT-DSL's CompiledKernel cannot be called directly. "
            "Use `kdt.launch_kernel()` to execute the kernel or `kdt.benchmark_kernel()` to benchmark it."
        )
    
class KernelFunction:
    """
    Wrapper for an (uncompiled) kernel function.
    """

    def __init__(self, func: Callable, num_jobs_calculator: Callable):
        self.func = func
        self.num_jobs_calculator = num_jobs_calculator

    def compile(self, task_args: Dict[str, Any], io_tensors: Dict[str, torch.Tensor]) -> CompiledKernel:
        """
        Compile the kernel function into IR
        """
        io_tensors_meta = {name: IOTensorMeta.from_tensor(tensor) for name, tensor in io_tensors.items()}
        _, start_lineno = inspect.findsource(self.func)
        compiler = FrontendCompiler()
        compiled_kernel = compiler.compile(
            self.func,
            self.num_jobs_calculator,
            task_args,
            io_tensors_meta
        )
        return CompiledKernel(compiled_kernel, task_args, io_tensors_meta, start_lineno)

    def __call__(self, *args, **kwargs):
        raise SemanticError(
            "KDT-DSL's KernelFunction functions cannot be called directly. "
            "Use .compile() to compile the kernel."
        )
    

class FrontendCompiler:
    """Compiles Python functions with @kdt.kernel decorator to KDT-DSL IR."""

    def __init__(self):
        pass

    def compile(
        self,
        func: Callable,
        num_jobs_calculator: Callable,
        task_args: Dict[str, Any],
        io_tensors_meta: Dict[str, IOTensorMeta]
    ) -> Kernel:
        """
        Compile a kernel function to IR.

        Args:
            func: Python function decorated with @kdt.kernel
            num_jobs_calculator: Function to calculate number of jobs (provided via decorator)
            task_args: Task arguments for num_jobs_calculator execution (optional)

        Returns:
            Kernel IR object
        """
        # Get source code and AST tree
        _, start_lineno = inspect.findsource(func)
        source = inspect.getsource(func)
        module = ast.parse(source)

        # Extract function definition, and validate
        func_def = None
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                func_def = node
        if func_def is None:
            raise CompilationError("No function definition found")
        self._validate_kernel_signature(func_def)

        # Sanity check for `task_args`
        for key, value in task_args.items():
            if not isinstance(value, int):
                raise ConstantRequiredError(
                    f"task_args['{key}'] must be an integer constant, got {type(value).__name__}"
                )
        
        # Initialize symbol table with kernel parameters
        symbol_table = SymbolTable()
        symbol_table.define('task_args', SymbolInfo(
            name = 'task_args',
            var_type = VarType.DICT,
            data = task_args
        ))
        io_tile_storage_defs = []
        for name, meta in io_tensors_meta.items():
            io_tile_storage_defs.append(TileStorage(
                shape=list(meta.shape),
                dtype=meta.dtype,
                space=MemorySpace.GLOBAL,
                name=name
            ))
        symbol_table.define('io_tensors', SymbolInfo(
            name = 'io_tensors',
            var_type = VarType.DICT,
            data = {
                tile_storage.name: tile_storage.get_view()
                for tile_storage in io_tile_storage_defs
            }
        ))

        # Define global scalars in symbol table

        # Traverse AST to generate IR
        visitor = ASTVisitor(symbol_table, start_lineno)
        visitor.visit(func_def)

        # Execute num_jobs_calculator
        num_jobs = self._calculate_num_jobs(num_jobs_calculator, task_args)

        # Create Kernel IR object
        kernel_ir = Kernel(
            name=func.__name__,
            io_tile_storage_defs=io_tile_storage_defs,
            spm_tile_storage_defs=visitor.spm_tile_storage_defs,
            body=Block(visitor.current_instructions),
            num_jobs=num_jobs
        )

        return kernel_ir

    def _validate_kernel_signature(self, func_def: ast.FunctionDef) -> None:
        """Validate kernel function signature."""
        # Check number of parameters
        if len(func_def.args.args) != 2:
            raise CompilationError(
                f"Kernel function must have exactly 2 parameters, got {len(func_def.args.args)}"
            )

        # Check parameter names
        param_names = [arg.arg for arg in func_def.args.args]
        expected = ['task_args', 'io_tensors']
        for i, (actual, expected_name) in enumerate(zip(param_names, expected)):
            if actual != expected_name:
                raise CompilationError(
                    f"Parameter {i} should be named '{expected_name}', got '{actual}'"
                )

    def _calculate_num_jobs(
        self,
        num_jobs_calculator: Callable,
        task_args: Optional[Dict[str, Any]]
    ) -> int:
        """Calculate number of jobs using num_jobs_calculator."""
        if task_args is None:
            task_args = {}

        try:
            result = num_jobs_calculator(task_args)
        except Exception as e:
            raise CompilationError(
                f"Failed to execute num_jobs_calculator: {e}"
            ) from e

        if not isinstance(result, int):
            raise CompilationError(
                f"num_jobs_calculator must return integer, got {type(result).__name__}"
            )

        if result <= 0:
            raise CompilationError(
                f"num_jobs_calculator must return positive integer, got {result}"
            )

        return result
