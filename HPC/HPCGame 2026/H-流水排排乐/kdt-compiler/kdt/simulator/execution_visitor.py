"""
Execution visitor for KDT-DSL IR.

Visits IR nodes and executes them using NumPy operations.
"""

import dataclasses
import math
import enum
import time
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
import numpy as np
from ..ir import Copy
from kdt.ir import *
from kdt.ir.ir_visitor import AutoRecursiveIRVisitor
from kdt.ir.errors import *
from .execution_context import ExecutionContext
from .tpu_spec import TPUSpec

@dataclasses.dataclass
class GetTileDataRequest:
    tile: Tile
    is_output: bool = False
    memory_space: MemorySpace = MemorySpace.SPM

class HardwareQueue(enum.Enum):
    """
    Represent the hardware queue type for instruction execution.
    """
    VXM = "VXM"
    MXM = "MXM"

def pad_to(a: int, b: int):
    return (a+b-1)//b*b

class ExecutionVisitor(AutoRecursiveIRVisitor):
    """
    Visitor that executes KDT-DSL IR using NumPy.

    This visitor evaluates expressions to scalar values and executes instructions
    using NumPy operations on array views.

    Attributes:
        context: ExecutionContext for current job
    """

    def __init__(self, context: ExecutionContext, tpu_spec: TPUSpec, end_time_limit: float):
        super().__init__()
        self.context = context
        self.tpu_spec = tpu_spec
        self.end_time_limit = end_time_limit
        self.last_instr_finish_cycle = 0
        self.last_instr_finish_cycle_in_hardware_queues: Dict[HardwareQueue, int] = {
            HardwareQueue.VXM: 0,
            HardwareQueue.MXM: 0,
        }

    def get_cycle_usage(self) -> int:
        """Get total cycle usage of the executed job."""
        return self.last_instr_finish_cycle
    
    # ----------------------------------------------------------------------
    # Expression evaluation
    # ----------------------------------------------------------------------

    def visit_ConstantExpr(self, node: ConstantExpr) -> Union[int, float, bool]:
        """Evaluate constant expression."""
        return node.value

    def visit_GetJobIdExpr(self, node: GetJobIdExpr) -> int:
        """Evaluate job ID expression."""
        return self.context.job_id

    def visit_LoopVarExpr(self, node: LoopVarExpr) -> Any:
        return self.context.get_loop_var(node.name)
    
    def visit_UnaryExpr(self, node: UnaryExpr) -> Union[int, float, bool]:
        """Evaluate unary expression."""
        operand = node.operand.accept(self)
        if node.op == UnaryExprOp.NEG:
            return -operand
        elif node.op == UnaryExprOp.NOT:
            return not operand
        else:
            raise InternalError(f"Unsupported operation: {node.op}")

    def visit_BinaryExpr(self, node: BinaryExpr) -> Union[int, float, bool]:
        """Evaluate binary expression."""
        left = node.left.accept(self)
        right = node.right.accept(self)
        op = node.op

        # Implement operations matching IR's as_constant logic
        if op == BinaryExprOp.ADD:
            return left + right
        elif op == BinaryExprOp.SUB:
            return left - right
        elif op == BinaryExprOp.MUL:
            return left * right
        elif op == BinaryExprOp.FLOOR_DIV:
            if right == 0:
                raise ValueError("Division by zero in FLOOR_DIV")
            return left // right
        elif op == BinaryExprOp.DIV:
            if right == 0:
                raise ValueError("Division by zero in DIV")
            return left / right
        elif op == BinaryExprOp.MOD:
            if right == 0:
                raise ValueError("Division by zero in MOD")
            return left % right
        elif op == BinaryExprOp.BITWISE_AND:
            if isinstance(left, float) or isinstance(right, float):
                raise TypeError("BITWISE_AND only supports boolean or integer operands")
            return left & right
        elif op == BinaryExprOp.BITWISE_OR:
            if isinstance(left, float) or isinstance(right, float):
                raise TypeError("BITWISE_OR only supports boolean or integer operands")
            return left | right
        elif op == BinaryExprOp.BITWISE_XOR:
            if isinstance(left, float) or isinstance(right, float):
                raise TypeError("BITWISE_XOR only supports boolean or integer operands")
            return left ^ right
        elif op == BinaryExprOp.LOGICAL_AND:
            return left and right
        elif op == BinaryExprOp.LOGICAL_OR:
            return left or right
        elif op == BinaryExprOp.LSHIFT:
            if isinstance(left, float) or isinstance(right, float):
                raise TypeError("LSHIFT only supports integer operands")
            return left << right
        elif op == BinaryExprOp.RSHIFT:
            if isinstance(left, float) or isinstance(right, float):
                raise TypeError("RSHIFT only supports integer operands")
            return left >> right
        else:
            raise InternalError(f"Unsupported binary expression operation: {op}")

    def visit_CompareExpr(self, node: CompareExpr) -> bool:
        """Evaluate comparison expression."""
        left = node.left.accept(self)
        right = node.right.accept(self)
        op = node.op

        if op == CompareExprOp.LE:
            return left < right
        elif op == CompareExprOp.LEQ:
            return left <= right
        elif op == CompareExprOp.EQ:
            return left == right
        elif op == CompareExprOp.NEQ:
            return left != right
        else:
            raise InternalError(f"Unsupported compare expression operation: {op}")
        
    # ----------------------------------------------------------------------
    # Tile and TileStorage visiting (no-op for execution)
    # ----------------------------------------------------------------------

    def visit_TileStorage(self, node: TileStorage):
        """TileStorage nodes don't need execution."""
        pass

    def visit_Tile(self, node: Tile):
        """Tile nodes don't need execution."""
        pass

    # ----------------------------------------------------------------------
    # Helper methods for tile data access
    # ----------------------------------------------------------------------

    def _get_tile_data_and_issuable_cycle_and_update_release_cycle(self, requests: List[GetTileDataRequest], instr_latency_calculator: Callable, hardware_queue: Optional[HardwareQueue] = None, update_isu_issue_cycle: bool = True) -> Tuple[List[np.ndarray], int]:
        """
        This function:
        - Get tile data arrays
        - Get the earliest issuable cycle of the current instruction, according to write_release_time and read_release_time of involved tiles
        - Update the read_release_time and write_release_time of involved tiles after the instruction is issued
        - Update self.context.nxt_isu_issue_cycle (if `update_isu_issue_cycle` is True)
        - Update self.last_instr_finish_cycle

        `instr_latency_calculator` should be a callable that takes a list of all data chunks and returns the instruction execution time in cycles.
        """
        resolved_chunks = []    # (data_chunk, write_release_time_chunk, read_release_time_chunk) of every request
        issue_cycle_constraints = [
            self.context.get_nxt_isu_issue_cycle()
        ]

        if hardware_queue is not None:
            issue_cycle_constraints.append(self.last_instr_finish_cycle_in_hardware_queues[hardware_queue])

        for request in requests:
            tile = request.tile
            memory_space = request.memory_space

            if memory_space == MemorySpace.GLOBAL:
                storage_state = self.context.get_global_array(tile.storage)
            else:
                storage_state = self.context.get_spm_array(tile.storage)

            # Evaluate shape dimensions to integers
            shape = []
            for dim_expr in tile.shape.dims:
                dim_val = dim_expr.accept(self)
                if not isinstance(dim_val, int):
                    raise TypeError(f"Shape dimension must be integer, got {type(dim_val)}")
                if dim_val < 0:
                    raise ValueError(f"Shape dimension must be non-negative, got {dim_val}")
                shape.append(dim_val)

            # Evaluate start index
            base_array = storage_state.array
            start_offset = tile.start_index.accept(self)
            if not isinstance(start_offset, int):
                raise TypeError(f"Start index must be integer, got {type(start_offset)}")
            if start_offset < 0 or start_offset + sum([(a-1)*b for (a, b) in zip(shape, tile.strides)]) >= base_array.size:
                raise IndexError(f"Start index {start_offset} with shape {shape}, stride {tile.strides} out of bounds for storage with size {base_array.size}. Check whether your buffer access is out-of-bound.")

            data_chunk = self._get_chunk(base_array, shape, tile.strides, start_offset)
            write_release_time_chunk = self._get_chunk(storage_state.write_release_time, shape, tile.strides, start_offset)
            read_release_time_chunk = self._get_chunk(storage_state.read_release_time, shape, tile.strides, start_offset)
            resolved_chunks.append((data_chunk, write_release_time_chunk, read_release_time_chunk))

            # Get issue cycle
            issue_cycle_constraints.append(np.max(write_release_time_chunk, initial=0))   # 不论是读取还是写入，都需要等待上一次写入完成，防止 WAR 和 WAW 冲突
            if request.is_output:
                # 需要等待上一次读取完成，防止 RAW 冲突
                issue_cycle_constraints.append(np.max(read_release_time_chunk, initial=0))
            
        issue_cycle = int(max(issue_cycle_constraints))
        data_chunks = [x for (x, _, _) in resolved_chunks]

        # Update release times
        instr_exec_time = instr_latency_calculator(data_chunks)
        finish_cycle = issue_cycle + instr_exec_time
        for (data_chunk, write_release_time_chunk, read_release_time_chunk), request in zip(resolved_chunks, requests):
            if request.is_output:
                # Output tile: update write_release_time
                write_release_time_chunk[...] = finish_cycle
            else:
                # Input tile: update read_release_time
                read_release_time_chunk[...] = finish_cycle

        # Update ISU next issue cycle
        if update_isu_issue_cycle:
            self.context.nxt_isu_issue_cycle = issue_cycle+1

        # Update self.last_instr_finish_cycle
        self.last_instr_finish_cycle = max(self.last_instr_finish_cycle, finish_cycle)

        # Update hardware queue finish cycle
        if hardware_queue is not None:
            self.last_instr_finish_cycle_in_hardware_queues[hardware_queue] = max(
                self.last_instr_finish_cycle_in_hardware_queues[hardware_queue],
                finish_cycle
            )

        return (data_chunks, issue_cycle)

    def _get_chunk(self, base_array: np.ndarray, shape: List[int], strides: List[int], start_offset: int) -> np.ndarray:
        """
        Get NumPy array view for a base_array with given shape and start offset.

        Args:
            base_array: Base NumPy array, acquired from self.context.get_XXX_array().array
            shape: List of shape dimensions, evaluated
            strides: List of strides in elements
            start_offset: Start index offset in elements, evaluated

        Returns:
            NumPy array view with appropriate shape and strides
        """
        # Convert strides from elements to bytes
        item_size = base_array.itemsize
        strides_bytes = [s * item_size for s in strides]

        # Create strided view with offset
        offset_bytes = start_offset * item_size
        view = np.ndarray(
            shape=shape,
            dtype=base_array.dtype,
            buffer=base_array.data,
            offset=offset_bytes,
            strides=strides_bytes
        )
        return view

    # ----------------------------------------------------------------------
    # Instruction execution
    # ----------------------------------------------------------------------

    def visit_Unary(self, node: Unary):
        """Execute unary operation: exp, log, pow."""
        [x_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.x),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(chunks[0].size / self.tpu_spec.vxm_trpt),
            HardwareQueue.VXM
        )
        y_value = node.y.accept(self)

        if x_data.shape != out_data.shape:
            raise ShapeError(f"Shape mismatch in {node.op.name} operation: x shape {x_data.shape}, out shape {out_data.shape}")

        if node.op == UnaryOp.EXP:
            # out = y ** x
            if y_value <= 0:
                raise ValueError(f"Base y must be positive for exp operation, got {y_value}")
            out_data[...] = np.power(np.full_like(x_data, y_value), x_data)
        elif node.op == UnaryOp.LOG:
            # out = log_y(x) = log(x) / log(y)
            if y_value <= 0 or y_value == 1:
                raise ValueError(f"Base y must be positive and not equal to 1 for log operation, got {y_value}")
            out_data[...] = np.log(x_data, np.full_like(x_data, y_value))
        elif node.op == UnaryOp.POW:
            # out = x ** y
            out_data[...] = np.power(x_data, np.full_like(x_data, y_value))
        else:
            raise InternalError(f"Unsupported unary operation: {node.op}")

    def visit_Binary(self, node: Binary):
        """Execute binary elementwise operation."""
        [a_data, b_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.a),
                GetTileDataRequest(node.b),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(chunks[0].size / self.tpu_spec.vxm_trpt),
            HardwareQueue.VXM
        )
        
        if not a_data.shape == b_data.shape == out_data.shape:
            raise ShapeError(f"Shape mismatch in binary operation {node.op.name}: a shape {a_data.shape}, b shape {b_data.shape}, out shape {out_data.shape}")

        if node.op == BinaryOp.ADD:
            out_data[...] = a_data + b_data
        elif node.op == BinaryOp.SUB:
            out_data[...] = a_data - b_data
        elif node.op == BinaryOp.MUL:
            out_data[...] = a_data * b_data
        elif node.op == BinaryOp.DIV:
            out_data[...] = a_data / b_data
        elif node.op == BinaryOp.MAX:
            out_data[...] = np.maximum(a_data, b_data)
        elif node.op == BinaryOp.MIN:
            out_data[...] = np.minimum(a_data, b_data)
        elif node.op == BinaryOp.AND:
            out_data[...] = np.logical_and(a_data, b_data)
        elif node.op == BinaryOp.OR:
            out_data[...] = np.logical_or(a_data, b_data)
        else:
            raise InternalError(f"Unsupported binary operation: {node.op}")

    def visit_Compare(self, node: Compare):
        """Execute comparison operation."""
        [a_data, b_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.a),
                GetTileDataRequest(node.b),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(chunks[0].size / self.tpu_spec.vxm_trpt),
            HardwareQueue.VXM
        )

        if not a_data.shape == b_data.shape == out_data.shape:
            raise ShapeError(f"Shape mismatch in compare operation {node.op.name}: a shape {a_data.shape}, b shape {b_data.shape}, out shape {out_data.shape}")

        if node.op == CompareOp.LE:
            out_data[...] = a_data < b_data
        elif node.op == CompareOp.LEQ:
            out_data[...] = a_data <= b_data
        elif node.op == CompareOp.EQ:
            out_data[...] = a_data == b_data
        elif node.op == CompareOp.NEQ:
            out_data[...] = a_data != b_data
        else:
            raise InternalError(f"Unsupported compare operation: {node.op}")

    def visit_MatMul(self, node: MatMul):
        """Execute matrix multiplication."""
        [a_data, b_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.a),
                GetTileDataRequest(node.b),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(pad_to(chunks[0].shape[0], 128)*pad_to(chunks[0].shape[1], 16)*pad_to(chunks[1].shape[1], 128) / self.tpu_spec.mxm_trpt),
            HardwareQueue.MXM
        )
        is_accumulate = node.accumulate.accept(self)

        if a_data.ndim != 2 or b_data.ndim != 2 or out_data.ndim != 2:
            raise ShapeError(f"matmul operands must be 2D matrices: a shape {a_data.shape}, b shape {b_data.shape}, out shape {out_data.shape}")
        
        if a_data.shape[0] != out_data.shape[0] or b_data.shape[1] != out_data.shape[1] or a_data.shape[1] != b_data.shape[0]:
            raise ShapeError(f"Shape mismatch in matmul operation: a shape {a_data.shape}, b shape {b_data.shape}, out shape {out_data.shape}")

        if is_accumulate:
            out_data[...] += np.matmul(a_data, b_data)
        else:
            out_data[...] = np.matmul(a_data, b_data)

    def visit_FMA(self, node: FMA):
        """Execute fused multiply-add: out = a * b + c."""
        [a_data, b_data, c_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.a),
                GetTileDataRequest(node.b),
                GetTileDataRequest(node.c),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(chunks[0].size / self.tpu_spec.vxm_trpt),
            HardwareQueue.VXM
        )

        if not a_data.shape == b_data.shape == c_data.shape == out_data.shape:
            raise ShapeError(f"Shape mismatch in fma operation: a shape {a_data.shape}, b shape {b_data.shape}, c shape {c_data.shape}, out shape {out_data.shape}")

        out_data[...] = a_data * b_data + c_data

    def visit_Reduce(self, node: Reduce):
        [src_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.src),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda chunks: math.ceil(chunks[0].size / self.tpu_spec.vxm_trpt),
            HardwareQueue.VXM
        )

        data_shape = src_data.shape
        if node.dim < 0 or node.dim >= len(data_shape):
            raise ValueError(f"Reduction dimension {node.dim} out of bounds for data shape {data_shape}")
        
        data_shape = data_shape[:node.dim] + data_shape[node.dim+1:]
        if data_shape != out_data.shape:
            raise ShapeError(f"Shape mismatch in reduce operation: src shape {src_data.shape}, out shape {out_data.shape}, reduced dim {node.dim}")

        keepdims = False  # Output shape does not include reduced dimensions
        if node.op == 'sum':
            reduced = np.sum(src_data, axis=node.dim, keepdims=keepdims)
        elif node.op == 'max':
            reduced = np.max(src_data, axis=node.dim, keepdims=keepdims)
        elif node.op == 'min':
            reduced = np.min(src_data, axis=node.dim, keepdims=keepdims)
        else:
            raise InternalError(f"Unsupported reduction operation: {node.op}")

        out_data[...] = reduced

    def visit_Where(self, node: Where):
        [cond_data, a_data, b_data, out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.cond),
                GetTileDataRequest(node.a),
                GetTileDataRequest(node.b),
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda x: 0,
            update_isu_issue_cycle=False
        )

        if not cond_data.shape == a_data.shape == b_data.shape == out_data.shape:
            raise ShapeError(f"Shape mismatch in where operation: cond shape {cond_data.shape}, a shape {a_data.shape}, b shape {b_data.shape}, out shape {out_data.shape}")

        out_data[...] = np.where(cond_data, a_data, b_data)

    def visit_Copy(self, node: Copy) -> Any:
        [src_data, dst_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.src),
                GetTileDataRequest(node.dst, is_output=True),
            ],
            lambda x: 0,
            update_isu_issue_cycle=False
        )

        if src_data.shape != dst_data.shape:
            raise ShapeError(f"Shape mismatch in copy operation: src shape {src_data.shape}, dst shape {dst_data.shape}")

        dst_data[...] = src_data
        
    def visit_Fill(self, node: Fill):
        [out_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.out, is_output=True),
            ],
            lambda x: 0,
            update_isu_issue_cycle=False
        )
        out_data[...] = node.value

    def visit_Load(self, node: Load):
        [src_data, dst_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.src, memory_space=MemorySpace.GLOBAL),
                GetTileDataRequest(node.dst, is_output=True, memory_space=MemorySpace.SPM),
            ],
            lambda x: self.tpu_spec.load_store_latency
        )

        if src_data.shape != dst_data.shape:
            raise ShapeError(f"Shape mismatch in load operation: src shape {src_data.shape}, dst shape {dst_data.shape}")

        dst_data[...] = src_data

    def visit_Store(self, node: Store):
        [src_data, dst_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.src, memory_space=MemorySpace.SPM),
                GetTileDataRequest(node.dst, is_output=True, memory_space=MemorySpace.GLOBAL),
            ],
            lambda x: self.tpu_spec.load_store_latency
        )

        if src_data.shape != dst_data.shape:
            raise ShapeError(f"Shape mismatch in store operation: src shape {src_data.shape}, dst shape {dst_data.shape}")

        dst_data[...] = src_data

    def visit_Print(self, node: Print):
        if node.print_only_if_job0 and self.context.job_id != 0:
            return
        [tile_data], issue_cycle = self._get_tile_data_and_issuable_cycle_and_update_release_cycle(
            [
                GetTileDataRequest(node.tile),
            ],
            lambda x: 0,
            update_isu_issue_cycle=False
        )
        print(f"[Job {self.context.job_id}] {node.msg}: {tile_data}")

    def visit_Block(self, node: Block):
        for instr in node.instructions:
            if time.time() > self.end_time_limit:
                raise TimeoutError(f"Simulation exceeded time limit.")
            instr.accept(self)

    def visit_ForLoop(self, node: ForLoop):
        start = node.start.accept(self)
        end = node.end.accept(self)
        if not isinstance(start, int) or not isinstance(end, int):
            if time.time() > self.end_time_limit:
                raise TimeoutError(f"Simulation exceeded time limit.")
            raise TypeError(f"ForLoop bounds must be integers, got start={start}, end={end}")

        for i in range(start, end):
            self.context.set_loop_var(node.loop_var, i)
            node.body.accept(self)
        self.context.clear_loop_var(node.loop_var)

    def visit_IfElse(self, node: IfElse) -> Any:
        condition = node.condition.accept(self)
        if not isinstance(condition, bool):
            raise TypeError(f"IfElse condition must be boolean, got {type(condition)}")
        if condition:
            node.then_body.accept(self)
        elif node.else_body:
            node.else_body.accept(self)

    def visit_Kernel(self, node: Kernel):
        node.body.accept(self)