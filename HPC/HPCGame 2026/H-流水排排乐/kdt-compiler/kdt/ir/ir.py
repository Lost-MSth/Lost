import abc
from enum import Enum
from typing import List, Tuple, Union, Optional, Dict, TYPE_CHECKING
import copy


if TYPE_CHECKING:
    from kdt.ir.ir_visitor import IRVisitor  # 导入第二个文件的类型

class DataType(Enum):
    """Supported data types in KDT-DSL."""
    FLOAT32 = "float32"
    BOOL = "bool"

class MemorySpace(Enum):
    """Memory space where a tile resides."""
    GLOBAL = "global"  # Global memory (DRAM)
    SPM = "spm"        # Scratchpad memory in SM

class ConstantExprDataType(Enum):
    """Data types for constant expressions."""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"

    def is_matched_with_python_type(self, dtype) -> bool:
        if dtype == int:
            return self == ConstantExprDataType.INT
        elif dtype == float:
            return self == ConstantExprDataType.FLOAT
        elif dtype == bool:
            return self == ConstantExprDataType.BOOL
        else:
            return False

ExprValueT = Union[int, float, bool]

class UnaryExprOp(Enum):
    """Unary expression operations."""
    NEG = "-"
    NOT = "!"

class BinaryExprOp(Enum):
    """Binary expression operations."""
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    FLOOR_DIV = "//"
    MOD = "%"
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    BITWISE_XOR = "^"
    LOGICAL_AND = "&&"
    LOGICAL_OR = "||"
    LSHIFT = "<<"
    RSHIFT = ">>"

class CompareExprOp(Enum):
    """Comparison expression operations."""
    LE = "<"
    LEQ = "<="
    EQ = "=="
    NEQ = "!="

class UnaryOp(Enum):
    """Unary operations."""
    EXP = "exp"
    LOG = "log"
    POW = "pow"

class BinaryOp(Enum):
    """Binary operations."""
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MAX = "max"
    MIN = "min"
    AND = "and"
    OR = "or"

class CompareOp(Enum):
    """Comparison operations."""
    LE = "le"
    LEQ = "leq"
    EQ = "eq"
    NEQ = "neq"

# ----------------------------------------------------------------------
# IR Location Info
# ----------------------------------------------------------------------

class IRLoc:
    """
    Location information for IR nodes.
    """
    lineno: Optional[int] = None
    col_offset: Optional[int] = None

    def __init__(self, node = None):
        self.lineno = getattr(node, 'lineno', None)
        self.col_offset = getattr(node, 'col_offset', None)

from kdt.language.errors import IRException
from .errors import RuntimeError # To avoid circular import

# ----------------------------------------------------------------------
# Base IR Node
# ----------------------------------------------------------------------

class IRNode(abc.ABC):
    """
    The base class for all Intermediate Representation (IR) nodes.
    """
    def __init__(self, **kwargs):
        self.loc = kwargs.pop('loc', IRLoc())


    def accept(self, visitor: 'IRVisitor'):
        """
        Accept a visitor for traversing the IR tree.

        Args:
            visitor: The visitor instance to accept.

        Returns:
            The result of the visitor's visit method.
        """
        method_name = f"visit_{self.__class__.__name__}"
        method = getattr(visitor, method_name, getattr(visitor, 'generic_visit', None))

        if not method:
            raise NotImplementedError(
                f"Visitor {type(visitor).__name__} does not implement {method_name} "
                f"and lacks a generic_visit method."
            )
        
        try:
            return method(self)
        except RuntimeError as e:
            if not e.loc:
                e.loc = self.loc
            if not e.ast_start_lineno:
                context = getattr(visitor, "context", None)
                if context is not None:
                    e.ast_start_lineno = context.start_lineno
            raise

# ----------------------------------------------------------------------
# Expressions (for scalar value calculation)
# ----------------------------------------------------------------------

class Expr(IRNode):
    """Base class for scalar expressions."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abc.abstractmethod
    def as_constant(self) -> Optional[ExprValueT]:
        """
        Try to evaluate the expression as a constant integer.
        If not possible, return None.
        """
        raise NotImplementedError("as_constant not implemented for this Expr.")

    def is_constant(self) -> bool:
        return self.as_constant() is not None

class ConstantExpr(Expr):
    """Constant scalar value."""
    def __init__(self, dtype: ConstantExprDataType, value: ExprValueT, **kwargs):
        super().__init__(**kwargs)
        self.dtype = dtype
        self.value = value

    def __repr__(self):
        return f"ConstantExpr({self.dtype}, {self.value})"
    
    def __str__(self) -> str:
        return str(self.value)
    
    def as_constant(self) -> ExprValueT:
        return self.value


class GetJobIdExpr(Expr):
    """Expression representing the current job ID."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return "GetJobIdExpr()"

    def as_constant(self) -> None:
        return None


class LoopVarExpr(Expr):
    """Expression representing a loop variable."""
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def __repr__(self):
        return f"LoopVarExpr({self.name})"
    
    def __str__(self) -> str:
        return self.name
    
    def as_constant(self) -> None:
        return None
    
    
class UnaryExpr(Expr):
    """Unary operation on an expression."""
    def __init__(self, op: UnaryExprOp, operand: Expr, **kwargs):
        super().__init__(**kwargs)
        if op not in UnaryExprOp:
            raise IRException(f"Unsupported operation: {op}")
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryExpr({self.op}, {self.operand})"
    
    def __str__(self) -> str:
        return f"({self.op.value}{self.operand})"
    
    def as_constant(self) -> Optional[ExprValueT]:
        operand_val = self.operand.as_constant()
        if operand_val is None:
            return None
        if self.op == UnaryExprOp.NEG:
            return -operand_val
        elif self.op == UnaryExprOp.NOT:
            return not operand_val
        else:
            raise IRException(f"Unsupported operation: {self.op}")
    

class BinaryExpr(Expr):
    """Binary operation on two expressions."""
    def __init__(self, op: BinaryExprOp, left: Expr, right: Expr, **kwargs):
        super().__init__(**kwargs)
        if op not in BinaryExprOp:
            raise IRException(f"Unsupported operation: {op}")
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryExpr({self.left}, {self.op}, {self.right})"
    
    def __str__(self) -> str:
        return f"({self.left} {self.op.value} {self.right})"
    
    def as_constant(self) -> Optional[ExprValueT]:
        left_val = self.left.as_constant()
        right_val = self.right.as_constant()
        if left_val is None or right_val is None:
            return None
        if self.op == BinaryExprOp.ADD:
            return left_val + right_val
        elif self.op == BinaryExprOp.SUB:
            return left_val - right_val
        elif self.op == BinaryExprOp.MUL:
            return left_val * right_val
        elif self.op == BinaryExprOp.FLOOR_DIV:
            if right_val == 0:
                raise IRException("Division by zero in BinaryExpr.FLOOR_DIV.")
            return left_val // right_val
        elif self.op == BinaryExprOp.DIV:
            if right_val == 0:
                raise IRException("Division by zero in BinaryExpr.DIV.")
            return left_val / right_val
        elif self.op == BinaryExprOp.MOD:
            if right_val == 0:
                raise IRException("Division by zero in BinaryExpr.MOD.")
            return left_val % right_val
        elif self.op == BinaryExprOp.BITWISE_AND:
            if isinstance(left_val, float) or isinstance(right_val, float):
                raise IRException("BinaryExpr.AND only supports boolean or integer operands.")
            return left_val & right_val
        elif self.op == BinaryExprOp.BITWISE_OR:
            if isinstance(left_val, float) or isinstance(right_val, float):
                raise IRException("BinaryExpr.OR only supports boolean or integer operands.")
            return left_val | right_val
        elif self.op == BinaryExprOp.BITWISE_XOR:
            if isinstance(left_val, float) or isinstance(right_val, float):
                raise IRException("BinaryExpr.XOR only supports boolean or integer operands.")
            return left_val ^ right_val
        elif self.op == BinaryExprOp.LOGICAL_AND:
            return left_val and right_val
        elif self.op == BinaryExprOp.LOGICAL_OR:
            return left_val or right_val
        elif self.op == BinaryExprOp.LSHIFT:
            if isinstance(left_val, float) or isinstance(right_val, float):
                raise IRException("BinaryExpr.LSHIFT only supports integer operands.")
            return left_val << right_val
        elif self.op == BinaryExprOp.RSHIFT:
            if isinstance(left_val, float) or isinstance(right_val, float):
                raise IRException("BinaryExpr.RSHIFT only supports integer operands.")
            return left_val >> right_val
        else:
            raise IRException(f"Unsupported operation: {self.op}")

class CompareExpr(Expr):
    """Comparison operation on two expressions."""
    def __init__(self, op: CompareExprOp, left: Expr, right: Expr, **kwargs):
        super().__init__(**kwargs)
        if op not in CompareExprOp:
            raise IRException(f"Unsupported operation: {op}")
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"CompareExpr({self.left}, {self.op}, {self.right})"
    
    def __str__(self) -> str:
        return f"({self.left} {self.op.value} {self.right})"
    
    def as_constant(self) -> Optional[ExprValueT]:
        left_val = self.left.as_constant()
        right_val = self.right.as_constant()
        if left_val is None or right_val is None:
            return None
        if self.op == CompareExprOp.LE:
            return left_val < right_val
        elif self.op == CompareExprOp.LEQ:
            return left_val <= right_val
        elif self.op == CompareExprOp.EQ:
            return left_val == right_val
        elif self.op == CompareExprOp.NEQ:
            return left_val != right_val
        else:
            raise IRException(f"Unsupported operation: {self.op}")
        
# ----------------------------------------------------------------------
# Shape
# ----------------------------------------------------------------------

class Shape:
    """Shape of a tile as a tuple of integers."""
    def __init__(self, dims: Union[Tuple[Expr, ...], List[Expr]]):
        if isinstance(dims, Tuple):
            dims = list(dims)
        assert len(dims) >= 1
        self.dims = dims

    def __repr__(self):
        return f"Shape{self.dims}"
    
    def __str__(self):
        res = ""
        for item in self.dims:
            res += str(item)
            res += ', '
        return f"Shape[{res[:-2]}]"
    
    def __eq__(self, other):
        return isinstance(other, Shape) and self.dims == other.dims

    def __hash__(self):
        return hash(self.dims)

    def __getitem__(self, index: int) -> Expr:
        return self.dims[index]
    
    def __setitem__(self, index: int, value: Expr):
        self.dims[index] = value

    @property
    def size(self) -> Expr:
        """Total number of elements."""
        product = ConstantExpr(ConstantExprDataType.INT, 1)
        for d in self.dims:
            product = BinaryExpr(BinaryExprOp.MUL, product, d)
        return product

    @property
    def ndim(self) -> int:
        """Number of dimensions."""
        return len(self.dims)

# ----------------------------------------------------------------------
# Tile references
# ----------------------------------------------------------------------

class TileStorage(IRNode):
    """
    The backend storage of a tile.
    Its shape must be static (int constants)
    """
    _counter = 0 # counter for anonymous storages
    def __init__(self, shape: List[int], dtype: DataType, space: MemorySpace, name: str, **kwargs):
        super().__init__(**kwargs)
        self.shape = shape
        self.shape_as_Shape = Shape([ConstantExpr(ConstantExprDataType.INT,dim) for dim in shape]) # type: ignore
        self.dtype = dtype
        self.space = space
        if name == "" :
            __class__._counter += 1
            self.name = f"_{__class__._counter}"
        else:
            self.name = name

    def get_view(self) -> 'Tile':
        """
        Get a full view of this tile storage.
        """
        return Tile(self, self.shape_as_Shape)
    
    def __repr__(self):
        return f"TileStorage(name={self.name}, shape={self.shape}, dtype={self.dtype}, space={self.space})"

class Tile(IRNode):
    """
    A view into a tile storage, possibly with slicing or broadcasting

    Each Tile has a backend TileStorage (which is the actual data located on DRAM/SPM), possibly with non-trival start indices and strides to represent a sub-tile, broadcasting, etc.
    """
    def __init__(self,
                 storage: TileStorage,
                 shape: Shape,
                 start_index: Optional[Expr] = None,
                 strides: Optional[List[int]] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.is_trival_start_index = start_index is None  # For `__repr__()`
        self.is_trival_strides = strides is None
        if start_index is None:
            start_index = ConstantExpr(ConstantExprDataType.INT, 0)
        if strides is None:
            # Construct default strides (contiguous layout), but only possible when all shape dims are Constant.
            static_shape = []
            for i in range(shape.ndim):
                cur_dim = shape[i].as_constant()
                if cur_dim is None:
                    raise IRException("Strides must be provided if shape dimensions are not all Constant.")
                if not isinstance(cur_dim, int):
                    raise IRException("Shape must be integers")
                static_shape.append(cur_dim)
            temp_strides: List[int] = []
            cur_stride = 1
            for i in range(shape.ndim-1, -1, -1):
                temp_strides.append(cur_stride)
                cur_stride *= static_shape[i]
            strides = list(reversed(temp_strides))
        self.storage = storage
        self.shape = shape
        self.start_index = start_index
        self.strides = strides

    def get_squeezed(self, dim: int):
        """
        Get a squeezed view by removing the given dim (which must be of size 1).
        """
        new_shape = copy.deepcopy(self.shape)
        del new_shape.dims[dim]
        new_strides = copy.deepcopy(self.strides)
        del new_strides[dim]
        return Tile(self.storage, new_shape, self.start_index, new_strides)
    
    def get_unsqueezed(self, dim: int):
        """
        Get an unsqueezed view by adding a size-1 dim at the given position.
        """
        new_shape = copy.deepcopy(self.shape)
        new_shape.dims.insert(dim, ConstantExpr(ConstantExprDataType.INT, 1))
        new_strides = copy.deepcopy(self.strides)
        new_strides.insert(dim, 0)  # Size-1 dimension has stride 0
        return Tile(self.storage, new_shape, self.start_index, new_strides)
    
    def get_sliced(self, dim: int, start: Expr, end: Expr):
        """
        Get a sliced view along the given dim from start to end.
        """
        new_shape = copy.deepcopy(self.shape)
        new_shape[dim] = BinaryExpr(BinaryExprOp.SUB, end, start)
        start_index_offset = BinaryExpr(BinaryExprOp.MUL, start, ConstantExpr(ConstantExprDataType.INT, self.strides[dim]))
        new_start_index = BinaryExpr(BinaryExprOp.ADD, self.start_index, start_index_offset)
        return Tile(self.storage, new_shape, new_start_index, self.strides)
    
    def get_transposed(self, dim0: int, dim1: int):
        """
        Get a transposed view by swapping axis0 and axis1.
        """
        new_shape = copy.deepcopy(self.shape)
        new_shape.dims[dim0], new_shape.dims[dim1] = new_shape.dims[dim1], new_shape.dims[dim0]
        new_strides = copy.deepcopy(self.strides)
        new_strides[dim0], new_strides[dim1] = new_strides[dim1], new_strides[dim0]
        return Tile(self.storage, new_shape, self.start_index, new_strides)
    
    def get_broadcasted(self, dim: int, new_size: Expr):
        """
        Get a broadcasted view to the new shape.
        """
        if self.shape[dim].as_constant() is not None and self.shape[dim].as_constant() != 1:
            raise IRException("Cannot broadcast dimension with size greater than 1.")
        # NOTE. If the broadcasted dimension size is not 1 and not constant, we cannot check it here. The behavior is undefined, as documented in `statement.md`
        new_shape = copy.deepcopy(self.shape)
        new_shape[dim] = new_size
        new_strides = copy.deepcopy(self.strides)
        new_strides[dim] = 0  # Broadcasting dimension has stride 0
        return Tile(self.storage, new_shape, self.start_index, new_strides)

    def get_indexed(self, dim: int, index: Expr):
        """
        Get an indexed view by fixing the given dim to index.
        """
        new_shape = copy.deepcopy(self.shape)
        del new_shape.dims[dim]
        index_offset = BinaryExpr(BinaryExprOp.MUL, index, ConstantExpr(ConstantExprDataType.INT, self.strides[dim]))
        new_start_index = BinaryExpr(BinaryExprOp.ADD, self.start_index, index_offset)
        new_strides = copy.deepcopy(self.strides)
        del new_strides[dim]
        return Tile(self.storage, new_shape, new_start_index, new_strides)
    
    def __repr__(self):
        res = f"Tile(storage={self.storage.name}, space={self.storage.space.name}, shape={self.shape}"
        if not self.is_trival_start_index:
            res += f", start_index={self.start_index}"
        if not self.is_trival_strides:
            res += f", strides={self.strides}"
        res += ')'
        return res
    
    def __getitem__(self, index: Union[int, slice, Tuple]) -> 'Tile':  # type: ignore
        """
        暂时定义一个空的 __getitem__ 操作，避免写 kernel 时 linter 报错
        """
        pass
    
# ----------------------------------------------------------------------
# Instructions
# ----------------------------------------------------------------------

class Instruction(IRNode):
    """
    Base class for all KDT-DSL instructions.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Unary(Instruction):
    """Base for unary elementwise operations."""
    def __init__(self, op: UnaryOp, x: Tile, out: Tile, y: Expr, **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.x = x
        self.out = out
        self.y = y  # y is `base` for `exp` and `log`, and is `y` for `pow`

    def __repr__(self):
        return f"{self.op}(x={self.x}, out={self.out}, y={self.y})"

class Binary(Instruction):
    """Base for binary elementwise operations."""
    def __init__(self, op: BinaryOp, a: Tile, b: Tile, out: Tile, **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.a = a
        self.b = b
        self.out = out

    def __repr__(self):
        return f"{self.op}(a={self.a}, b={self.b}, out={self.out})"

class Compare(Instruction):
    """Base for comparison operations."""
    def __init__(self, op: CompareOp, a: Tile, b: Tile, out: Tile, **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.a = a
        self.b = b
        self.out = out

    def __repr__(self):
        return f"{self.op}(a={self.a}, b={self.b}, out={self.out})"

class MatMul(Instruction):
    """
    kdt.matmul(a, b, out, accumulate=False)
    Matrix multiplication.
    """
    def __init__(self, a: Tile, b: Tile, out: Tile, accumulate: Expr, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b
        self.out = out
        self.accumulate = accumulate

    def __repr__(self):
        return f"MatMul(a={self.a}, b={self.b}, out={self.out}, accumulate={self.accumulate})"

class FMA(Instruction):
    """
    kdt.fma(a, b, c, out)
    Fused multiply-add: out = a * b + c
    """
    def __init__(self, a: Tile, b: Tile, c: Tile, out: Tile, **kwargs):
        super().__init__(**kwargs)
        self.a = a
        self.b = b
        self.c = c
        self.out = out

    def __repr__(self):
        return f"FMA(a={self.a}, b={self.b}, c={self.c}, out={self.out})"

class Reduce(Instruction):
    """
    kdt.reduce(x, dim, op, out)
    Reduces tile x along given dim with operation op.
    """
    def __init__(self, src: Tile, dim: int, op: str, out: Tile, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dim = dim
        self.op = op  # 'sum', 'max', 'min'
        self.out = out

    def __repr__(self):
        return f"Reduce(src={self.src}, dim={self.dim}, op={self.op}, out={self.out})"

# ----------------------------------------------------------------------
# Selection instructions
# ----------------------------------------------------------------------

class Where(Instruction):
    """
    kdt.where(cond, x, y, out)
    Selects elements from x or y based on condition cond.
    """
    def __init__(self, cond: Tile, a: Tile, b: Tile, out: Tile, **kwargs):
        super().__init__(**kwargs)
        self.cond = cond
        self.a = a
        self.b = b
        self.out = out

    def __repr__(self):
        return f"Where(cond={self.cond}, x={self.a}, y={self.b}, out={self.out})"


class Copy(Instruction):
    """
    kdt.copy(src, dst)
    Copies data from tile src to tile dst.
    """
    def __init__(self, src: Tile, dst: Tile, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dst = dst

    def __repr__(self):
        return f"Copy(src={self.src}, dst={self.dst})"
    

class Fill(Instruction):
    """
    kdt.fill(x, value)
    Fills tile x with scalar value.
    """
    def __init__(self, out: Tile, value: Union[float, bool], **kwargs):
        super().__init__(**kwargs)
        self.out = out
        self.value = value

    def __repr__(self):
        return f"Fill(out={self.out}, value={self.value})"


# ----------------------------------------------------------------------
# Data movement instructions
# ----------------------------------------------------------------------

class Load(Instruction):
    """
    kdt.load(src, dst)
    Loads from global memory to SPM.
    """
    def __init__(self, src: Tile, dst: Tile, **kwargs):
        super().__init__(**kwargs)
        # src should be in global memory, dst in SPM
        self.src = src
        self.dst = dst

    def __repr__(self):
        return f"Load(src={self.src}, dst={self.dst})"


class Store(Instruction):
    """
    kdt.store(src, dst)
    Stores from SPM to global memory.
    """
    def __init__(self, src: Tile, dst: Tile, **kwargs):
        super().__init__(**kwargs)
        # src should be in SPM, dst in global memory
        self.src = src
        self.dst = dst

    def __repr__(self):
        return f"Store(src={self.src}, dst={self.dst})"

# ----------------------------------------------------------------------
# Debug instructions
# ----------------------------------------------------------------------

class Print(Instruction):
    """
    kdt.print(...)
    Debug print instruction.
    """
    def __init__(self, tile: Tile, msg: str, print_only_if_job0: bool, **kwargs):
        super().__init__(**kwargs)
        self.tile = tile
        self.msg = msg
        self.print_only_if_job0 = print_only_if_job0

    def __repr__(self):
        return f"Print(tile={self.tile}, msg={self.msg}, print_only_if_job0={self.print_only_if_job0})"

# ----------------------------------------------------------------------
# Program structure
# ----------------------------------------------------------------------

class Block(IRNode):
    """
    Represents a basic block in the IR.
    """
    def __init__(self, instructions: List[Instruction], **kwargs):
        super().__init__(**kwargs)
        self.instructions = instructions

    def __repr__(self):
        return f"Block({len(self.instructions)} instructions)"


class ForLoop(Instruction):
    """
    Represents a for-loop in the IR.
    """
    def __init__(self, loop_var: str, start: Expr, end: Expr, body: Block, **kwargs):
        super().__init__(**kwargs)
        self.loop_var = loop_var
        self.start = start
        self.end = end
        self.body = body

    def __repr__(self):
        return f"ForLoop(var={self.loop_var}, start={self.start}, end={self.end}, body={self.body})"


class IfElse(Instruction):
    """
    Represents an if-else statement in the IR.
    """
    def __init__(self, condition: Expr, then_body: Block, else_body: Optional[Block] = None, **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

    def __repr__(self):
        return f"IfElse(condition={self.condition}, then_body={self.then_body}, else_body={self.else_body})"


class Kernel(IRNode):
    """
    Represents a KDT-DSL kernel function.
    """
    def __init__(self,
                 name: str,
                 io_tile_storage_defs: List[TileStorage],
                 spm_tile_storage_defs: List[TileStorage],
                 body: Block,
                 num_jobs: int,
                 **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.io_tile_storage_defs = io_tile_storage_defs
        self.spm_tile_storage_defs = spm_tile_storage_defs
        self.body = body
        self.num_jobs = num_jobs

    def __repr__(self):
        return f"Kernel(name={self.name})"
