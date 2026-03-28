"""
AST visitor for transforming Python AST to KDT-DSL IR.
"""

import ast
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
import dataclasses

import kdt.ir as ir
from kdt.ir import IRLoc
from kdt.language.errors import *
from kdt.language.symbol_table import SymbolTable, SymbolInfo, VarType

class InterpretOptions(Enum):
    NONE = "NONE"  # No interpretation, return raw AST node
    TILE = "TILE"   # Must be ir.Tile
    EXPR = "EXPR"   # Must be ir.Expr
    CONST = "CONST"   # Must be a compile-time constant
    CONST_INT = "CONST_INT" # Must be a compile-time constant of dtype `int`
    CONST_FLOAT = "CONST_FLOAT" # Must be a compile-time constant of dtype `float`
    CONST_BOOL = "CONST_BOOL" # Must be a compile-time constant of dtype `bool`
    STRING = "String"

@dataclasses.dataclass
class FuncArg:
    name: str
    interpret_as: InterpretOptions = InterpretOptions.NONE  # If present, run `_visit_expr` (or something else, depends on the value of `interpret_as`, check its type, and return its value)
    default_val: Optional[Any] = None

class ASTVisitor(ast.NodeVisitor):
    """Visits AST nodes and generates KDT-DSL IR."""

    # Mapping from kdt function names to IR instruction classes
    _KDT_INSTRUCTIONS = {
        'matmul': ir.MatMul,
        'fma': ir.FMA,
        'reduce': ir.Reduce,
        'where': ir.Where,
        'copy': ir.Copy,
        'fill': ir.Fill,
        'load': ir.Load,
        'store': ir.Store,
        'print': ir.Print,
    }

    _KDT_UNARY_INSTRUCTIONS = {
        'exp': ir.UnaryOp.EXP,
        'log': ir.UnaryOp.LOG,
        'pow': ir.UnaryOp.POW
    }

    _KDT_BINARY_INSTRUCTIONS = {
        'add': ir.BinaryOp.ADD,
        'sub': ir.BinaryOp.SUB,
        'mul': ir.BinaryOp.MUL,
        'div': ir.BinaryOp.DIV,
        'max': ir.BinaryOp.MAX,
        'min': ir.BinaryOp.MIN,
        'logical_and': ir.BinaryOp.AND,
        'logical_or': ir.BinaryOp.OR
    }

    _KDT_COMPARE_INSTRUCTIONS = {
        'le': ir.CompareOp.LE,
        'leq': ir.CompareOp.LEQ,
        'eq': ir.CompareOp.EQ,
        'neq': ir.CompareOp.NEQ
    }

    _KDT_ALL_INSTRUCTIONS = list(_KDT_INSTRUCTIONS.keys()) + list(_KDT_UNARY_INSTRUCTIONS.keys()) + list(_KDT_BINARY_INSTRUCTIONS.keys()) + list(_KDT_COMPARE_INSTRUCTIONS.keys())

    def __init__(self, symbol_table: SymbolTable, start_lineno: int):
        self.symbol_table = symbol_table
        self.start_lineno = start_lineno
        self.current_instructions: List[ir.Instruction] = []
        self.kernel_name: Optional[str] = None
        self.loop_depth = 0  # Flag to detect alloc_spm in loops
        self.if_depth = 0  # Flag to detect alloc_spm in `if`
        self.spm_tile_storage_defs: List[ir.TileStorage] = []

    def visit(self, node: ast.AST) -> Any:
        """Visit a node, catching exceptions to add line number info."""
        try:
            return super().visit(node)
        except CompilationError as e:
            if not e.node:
                e.node = node
            if not e.ast_start_lineno:
                e.ast_start_lineno = self.start_lineno
            raise

    def visit_Module(self, node: ast.Module) -> Any:
        """Visit module: process each statement."""
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """Visit function definition: the kernel function."""
        self.kernel_name = node.name
        # Enter function scope (already has kernel parameters from symbol table)
        self.symbol_table.push_scope()
        try:
            # Process body statements
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self.symbol_table.pop_scope()

    def visit_Assign(self, node: ast.Assign) -> Any:
        """Visit assignment statement."""
        if len(node.targets) != 1:
            raise UnsupportedFeatureError("Multiple assignment targets not supported")
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise UnsupportedFeatureError("Only simple variable assignments are supported")

        var_name = target.id
        value = self._visit_expr(node.value)

        # Handle different types of assignments
        if isinstance(value, ir.TileStorage):
            # Tile assignment (e.g., a = kdt.alloc_spm(...))
            # Create symbol info
            tile_storage: ir.TileStorage = value
            tile_view: ir.Tile = tile_storage.get_view()
            info = SymbolInfo(
                name=var_name,
                var_type=VarType.TILE,
                dtype=tile_storage.dtype,
                memory_space=tile_storage.space,
                shape=tile_view.shape,
                tile_view=tile_view,
                storage=tile_storage
            )
            self.symbol_table.define(var_name, info)
        elif isinstance(value, ir.Tile):
            # Tile view assignment (alias for another tile)
            tile_view: ir.Tile = value
            storage = tile_view.storage
            info = SymbolInfo(
                name=var_name,
                var_type=VarType.TILE,
                dtype=storage.dtype,
                memory_space=storage.space,
                shape=tile_view.shape,
                tile_view=tile_view,
                storage=storage
            )
            self.symbol_table.define(var_name, info)
        elif isinstance(value, ir.Expr):
            # Scalar assignment
            expr: ir.Expr = value
            info = SymbolInfo(
                name=var_name,
                var_type=VarType.SCALAR,
                dtype=None,
                memory_space=None,
                shape=None,
                value=expr
            )
            self.symbol_table.define(var_name, info)
        else:
            raise CompilationError(f"Unsupported assignment value type: {type(value)}")

    def visit_Expr(self, node: ast.Expr) -> Any:
        """Visit expression statement (e.g., function call)."""
        value = self._visit_expr(node.value)
        if isinstance(value, ir.Instruction):
            # Instruction call that doesn't assign result (e.g., kdt.add(...))
            # Already added to current_instructions
            pass
        elif isinstance(value, ir.Tile) or isinstance(value, ir.Expr):
            # Tile or scalar expression without assignment - ignore
            pass
        else:
            raise CompilationError(f"Unsupported expression statement: {type(value)}")

    def visit_For(self, node: ast.For) -> Any:
        """Visit for loop."""
        # Check that iter is a call to range()
        if not isinstance(node.iter, ast.Call) or not isinstance(node.iter.func, ast.Name) or node.iter.func.id != 'range':
            raise UnsupportedFeatureError("Only for loops with range() are supported")

        # Parse range arguments
        args = node.iter.args
        if len(args) == 1:
            start = ir.ConstantExpr(ir.ConstantExprDataType.INT, 0, loc=IRLoc(node.iter))
            end = self._resolve_expr(args[0])
        elif len(args) == 2:
            start = self._resolve_expr(args[0])
            end = self._resolve_expr(args[1])
        elif len(args) == 3:
            raise UnsupportedFeatureError("for loops with step argument are not supported")
        else:
            raise SyntaxError("range() must takes 1~3 arguments")

        # Loop variable
        if not isinstance(node.target, ast.Name):
            raise UnsupportedFeatureError("Only simple loop variables are supported")
        loop_var = node.target.id

        # Enter loop scope
        self.loop_depth += 1
        self.symbol_table.push_scope()
        self.symbol_table.define(loop_var, SymbolInfo(
            name=loop_var,
            var_type=VarType.LOOP_VAR
        ))

        # Process loop body
        loop_body_instructions = []
        old_instructions = self.current_instructions
        self.current_instructions = loop_body_instructions
        try:
            for stmt in node.body:
                self.visit(stmt)
        finally:
            self.current_instructions = old_instructions
            self.symbol_table.pop_scope()
            self.loop_depth -= 1

        # Create ForLoop IR node
        loop_block = ir.Block(loop_body_instructions, loc=IRLoc(node))
        for_loop = ir.ForLoop(loop_var, start, end, loop_block, loc=IRLoc(node))
        self._add_instruction(for_loop)

    def visit_If(self, node: ast.If) -> Any:
        """Visit if statement."""
        # Evaluate condition
        cond = self._visit_expr(node.test)
        # Save old instructions
        old_instructions = self.current_instructions
        # Then block
        self.current_instructions = []
        self.symbol_table.push_scope()
        self.if_depth += 1
        for stmt in node.body:
            self.visit(stmt)
        then_instructions = self.current_instructions
        self.symbol_table.pop_scope()
        self.if_depth -= 1
        # Else block
        else_instructions = []
        if node.orelse:
            self.current_instructions = []
            self.symbol_table.push_scope()
            self.if_depth += 1
            for stmt in node.orelse:
                self.visit(stmt)
            else_instructions = self.current_instructions
            self.symbol_table.pop_scope()
            self.if_depth -= 1
        # Restore old instructions, and create IfElse IR node
        self.current_instructions = old_instructions
        self._add_instruction(ir.IfElse(
            cond,
            ir.Block(then_instructions, loc=IRLoc(node)),
            ir.Block(else_instructions, loc=IRLoc(node)) if else_instructions else None,
            loc=IRLoc(node)
        ))

    def visit_Call(self, node: ast.Call) -> Any:
        """Visit function call."""
        # Check if this is a kdt.* call
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'kdt':
            # kdt.xxx() call
            # NOTE. 如果 kdt 被 import 为别的名字，这里就会失效，需要改进
            return self._visit_kdt_call(node)
        elif isinstance(node.func, ast.Name):
            # Direct function call (e.g., range())
            # Handled elsewhere
            raise UnsupportedFeatureError(f"Unsupported function call: {node.func.id}")
        else:
            raise UnsupportedFeatureError("Unsupported call expression")

    def _visit_kdt_call(self, node: ast.Call) -> Any:
        """Handle kdt.xxx() call."""
        func_attr = node.func.attr

        # Special cases
        if func_attr == 'alloc_spm':
            return self._handle_alloc_spm(node)
        elif func_attr == 'get_job_id':
            return self._handle_get_job_id(node)
        elif func_attr in ['squeeze', 'unsqueeze', 'broadcast_to', 'transpose', 'slice']:
            return self._handle_shape_operation(node)
        elif func_attr in self._KDT_ALL_INSTRUCTIONS:
            return self._handle_kdt_instruction(node)
        else:
            raise SyntaxError(f"Unsupported KDT-DSL function: kdt.{func_attr}")

    def _handle_alloc_spm(self, node: ast.Call) -> ir.TileStorage:
        """Handle kdt.alloc_spm(shape, init_value=0, dtype='float32')."""
        # Check not in loop
        if self.loop_depth > 0:
            raise SemanticError("kdt.alloc_spm cannot be called inside a loop")
        if self.if_depth > 0:
            raise SemanticError("kdt.alloc_spm cannot be called inside an if statement")

        # Parse arguments
        args = self._parse_func_call_args(node, [
            FuncArg("shape"),
            FuncArg("dtype", InterpretOptions.STRING, "float32"),
            FuncArg("name", InterpretOptions.STRING, ""),
            FuncArg("init_value", InterpretOptions.CONST, 0)
        ])
        dtype = ir.DataType(args['dtype'])
        init_value = args['init_value']
        if dtype == ir.DataType.FLOAT32:
            init_value = float(init_value)
        elif dtype == ir.DataType.BOOL:
            init_value = bool(init_value)
        else:
            raise TypeError(f"Unknown type for `alloc_spm`: {dtype}", node)

        shape_dims = self._parse_shape(args['shape'])
        const_dims = []
        for dim in shape_dims:
            const = dim.as_constant()
            if const is None:
                # Shape dimensions must be constant integers
                raise ConstantRequiredError("kdt.alloc_spm shape dimensions must be constant integers")
            const_dims.append(const)

        storage = ir.TileStorage(const_dims, dtype, ir.MemorySpace.SPM, args['name'], loc=IRLoc(node))
        view = storage.get_view()
        self._add_instruction(ir.Fill(view, init_value, loc=IRLoc(node)))
        self.spm_tile_storage_defs.append(storage)
        return storage

    def _handle_get_job_id(self, node: ast.Call) -> ir.Expr:
        """Handle kdt.get_job_id()."""
        if node.args or node.keywords:
            raise SyntaxError("kdt.get_job_id() takes no arguments")
        return ir.GetJobIdExpr(loc=IRLoc(node))

    def _handle_shape_operation(self, node: ast.Call) -> ir.Tile:
        """Handle shape operations: squeeze, unsqueeze, broadcast_to, transpose, slice."""
        method_name = node.func.attr
        if method_name == 'squeeze':
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim", InterpretOptions.CONST_INT)
            ])
            if args['dim'] < 0 or args['dim'] >= len(args['x'].shape.dims):
                raise IndexError(f"squeeze dim {args['dim']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            return args['x'].get_squeezed(args['dim'])
        elif method_name == 'unsqueeze':
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim", InterpretOptions.CONST_INT)
            ])
            if args['dim'] < 0 or args['dim'] > len(args['x'].shape.dims):
                raise IndexError(f"unsqueeze dim {args['dim']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            return args['x'].get_unsqueezed(args['dim'])
        elif method_name == 'broadcast_to':
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim", InterpretOptions.CONST_INT),
                FuncArg("new_size", InterpretOptions.EXPR)
            ])
            if args['dim'] < 0 or args['dim'] >= len(args['x'].shape.dims):
                raise IndexError(f"broadcast_to dim {args['dim']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            return args['x'].get_broadcasted(args['dim'], args['new_size'])
        elif method_name == 'transpose':
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim1", InterpretOptions.CONST_INT),
                FuncArg("dim2", InterpretOptions.CONST_INT)
            ])
            if args['dim1'] < 0 or args['dim1'] >= len(args['x'].shape.dims):
                raise IndexError(f"transpose dim1 {args['dim1']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            if args['dim2'] < 0 or args['dim2'] >= len(args['x'].shape.dims):
                raise IndexError(f"transpose dim2 {args['dim2']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            return args['x'].get_transposed(args['dim1'], args['dim2'])
        elif method_name == 'slice':
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim", InterpretOptions.CONST_INT),
                FuncArg("start", InterpretOptions.EXPR),
                FuncArg("end", InterpretOptions.EXPR)
            ])
            if args['dim'] < 0 or args['dim'] >= len(args['x'].shape.dims):
                raise IndexError(f"slice dim {args['dim']} out of range for tile with {len(args['x'].shape.dims)} dim(s)", node)
            return args['x'].get_sliced(args['dim'], args['start'], args['end'])
        else:
            raise InternalError(f"Shape operation {method_name} not yet implemented")

    def _handle_kdt_instruction(self, node: ast.Call) -> ir.Instruction:
        """Handle regular KDT-DSL instruction call."""
        method_name = node.func.attr

        if method_name in self._KDT_UNARY_INSTRUCTIONS:
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE),
                FuncArg("y", InterpretOptions.EXPR)
            ])
            instr = ir.Unary(
                self._KDT_UNARY_INSTRUCTIONS[method_name],
                args['x'],
                args['out'],
                args['y'],
                loc=IRLoc(node)
            )
        elif method_name in self._KDT_BINARY_INSTRUCTIONS:
            args = self._parse_func_call_args(node, [
                FuncArg("a", InterpretOptions.TILE),
                FuncArg("b", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE),
            ])
            instr = ir.Binary(
                self._KDT_BINARY_INSTRUCTIONS[method_name],
                args['a'],
                args['b'],
                args['out'],
                loc=IRLoc(node)
            )
        elif method_name in self._KDT_COMPARE_INSTRUCTIONS:
            args = self._parse_func_call_args(node, [
                FuncArg("a", InterpretOptions.TILE),
                FuncArg("b", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE),
            ])
            instr = ir.Compare(
                self._KDT_COMPARE_INSTRUCTIONS[method_name],
                args['a'],
                args['b'],
                args['out'],
                loc=IRLoc(node)
            )
        elif method_name == 'fma':
            args = self._parse_func_call_args(node, [
                FuncArg("a", InterpretOptions.TILE),
                FuncArg("b", InterpretOptions.TILE),
                FuncArg("c", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE),
            ])
            instr = ir.FMA(
                args['a'],
                args['b'],
                args['c'],
                args['out'],
                loc=IRLoc(node)
            )
        elif method_name == 'matmul':
            args = self._parse_func_call_args(node, [
                FuncArg("a", InterpretOptions.TILE),
                FuncArg("b", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE),
                FuncArg("accumulate", InterpretOptions.EXPR, ir.ConstantExpr(ir.ConstantExprDataType.BOOL, False))
            ])
            instr = ir.MatMul(
                args['a'],
                args['b'],
                args['out'],
                args['accumulate'],
                loc=IRLoc(node)
            )
        elif method_name == 'reduce':
            # reduce(x, dim, op, out)
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("dim", InterpretOptions.CONST_INT),
                FuncArg("op", InterpretOptions.STRING),
                FuncArg("out", InterpretOptions.TILE)
            ])
            instr = ir.Reduce(
                args['x'],
                args['dim'],
                args['op'],
                args['out'],
                loc=IRLoc(node)
            )
        elif method_name == 'where':
            # where(cond, a, b, out)
            args = self._parse_func_call_args(node, [
                FuncArg("cond", InterpretOptions.TILE),
                FuncArg("a", InterpretOptions.TILE),
                FuncArg("b", InterpretOptions.TILE),
                FuncArg("out", InterpretOptions.TILE)
            ])
            instr = ir.Where(
                args['cond'],
                args['a'],
                args['b'],
                args['out'],
                loc=IRLoc(node)
            )
        elif method_name == 'copy':
            # copy(src, dst)
            args = self._parse_func_call_args(node, [
                FuncArg("src", InterpretOptions.TILE),
                FuncArg("dst", InterpretOptions.TILE)
            ])
            instr = ir.Copy(
                args['src'],
                args['dst'],
                loc=IRLoc(node)
            )
        elif method_name == 'fill':
            # fill(x, value)
            args = self._parse_func_call_args(node, [
                FuncArg("out", InterpretOptions.TILE),
                FuncArg("value", InterpretOptions.CONST)
            ])
            instr = ir.Fill(
                args['out'],
                args['value'],
                loc=IRLoc(node)
            )
        elif method_name == 'load':
            # load(addr, out)
            args = self._parse_func_call_args(node, [
                FuncArg("src", InterpretOptions.TILE),
                FuncArg("dst", InterpretOptions.TILE)
            ])
            instr = ir.Load(
                args['src'],
                args['dst'],
                loc=IRLoc(node)
            )
        elif method_name == 'store':
            # store(addr, value)
            args = self._parse_func_call_args(node, [
                FuncArg("src", InterpretOptions.TILE),
                FuncArg("dst", InterpretOptions.TILE)
            ])
            instr = ir.Store(
                args['src'],
                args['dst'],
                loc=IRLoc(node)
            )
        elif method_name == 'print':
            # print(x, msg="", print_only_if_job0=False)
            args = self._parse_func_call_args(node, [
                FuncArg("x", InterpretOptions.TILE),
                FuncArg("msg", InterpretOptions.STRING, ""),
                FuncArg("print_only_if_job0", InterpretOptions.CONST_BOOL, False)
            ])
            instr = ir.Print(
                args['x'],
                args['msg'],
                args['print_only_if_job0'],
                loc=IRLoc(node)
            )
        else:
            raise InternalError("Unhandled KDT instruction")

        self._add_instruction(instr)
        return instr

    def _visit_expr(self, node: ast.expr) -> Any:
        """
        Visit expression and return appropriate value.
        Here "expr" can be a scalar expression or a tile view. Pay attention to the difference with `ir.Expr`
        """
        if isinstance(node, ast.Constant):
            return self._resolve_expr(node)
        elif isinstance(node, ast.Name):
            info = self._get_variable_info(node.id)
            if info.var_type == VarType.TILE:
                if info.tile_view is None:
                    raise SymbolError(f"Tile variable '{node.id}' has no view")
                return info.tile_view
            elif info.var_type == VarType.SCALAR:
                if info.value is None:
                    raise SymbolError(f"Scalar variable '{node.id}' has no value")
                return info.value
            elif info.var_type == VarType.DICT:
                return info.data
            elif info.var_type == VarType.LOOP_VAR:
                return self._resolve_expr(node)
            else:
                raise TypeError(
                    f"Unsupported variable type for expression: {info.var_type}",
                    node
                )
        elif isinstance(node, ast.Call):
            return self.visit_Call(node)
        elif isinstance(node, ast.UnaryOp) or isinstance(node, ast.BinOp) or isinstance(node, ast.Compare) or isinstance(node, ast.BoolOp):
            return self._resolve_expr(node)
        elif isinstance(node, ast.Subscript):
            return self._visit_subscript(node)
        else:
            raise UnsupportedFeatureError(
                f"Unsupported expression type: {node.__class__.__name__}",
                node
            )

    def _visit_subscript(self, node: ast.Subscript) -> Union[ir.Tile, ir.ConstantExpr]:
        """Handle subscript (slicing) operations."""
        value = self._visit_expr(node.value)
        if isinstance(value, Dict):
            # Dictionary indexing
            if not isinstance(node.value, ast.Name):
                raise TypeError(
                    "Only dictionary variables can be indexed with subscript",
                    node
                )
            dict_name = node.value.id
            key = ast.literal_eval(node.slice)
            if key not in value:
                raise KeyError(f"Key '{key}' not found in dictionary {dict_name}", node)
            val = value[key]
            if dict_name == 'task_args':
                if not isinstance(val, int):
                    raise TypeError(
                        f"task_args['{key}'] must be an integer constant, got {type(val).__name__}",
                        node
                    )
                return ir.ConstantExpr(ir.ConstantExprDataType.INT, val, loc=IRLoc(node))
            elif dict_name == 'io_tensors':
                if not isinstance(val, ir.Tile):
                    raise TypeError(
                        f"io_tensors['{key}'] must be a Tile, got {type(val).__name__}",
                        node
                    )
                return val
            else:
                raise TypeError(
                    f"Only 'task_args' and 'io_tensors' dictionaries can be indexed, got '{dict_name}'",
                    node
                )
        elif isinstance(value, ir.Tile):
            cur_slice = node.slice
            if not isinstance(cur_slice, ast.Tuple):
                cur_slice = ast.Tuple(elts=[cur_slice], ctx=ast.Load())

            if len(cur_slice.elts) > len(value.shape.dims):
                raise SemanticError(
                    "Too many indices for tile subscript",
                    node
                )
            new_value_dim_idx = 0
            for t in cur_slice.elts:
                if isinstance(t, ast.Slice):
                    # Slice operation
                    if t.step is not None:
                        raise UnsupportedFeatureError(
                            "Slice step not supported",
                            t
                        )
                    start = self._resolve_expr(t.lower) if t.lower else ir.ConstantExpr(ir.ConstantExprDataType.INT, 0, loc=IRLoc(t))
                    end = self._resolve_expr(t.upper) if t.upper else value.shape[new_value_dim_idx]
                    value = value.get_sliced(new_value_dim_idx, start, end)
                    new_value_dim_idx += 1
                elif isinstance(t, ast.Constant) and t.value is Ellipsis:
                    raise UnsupportedFeatureError(
                        "Ellipsis (...) not supported in subscript",
                        t
                    )
                else:
                    cur_index = self._resolve_expr(t)
                    value = value.get_indexed(new_value_dim_idx, cur_index)
                    # Note: after indexing, the dimension is removed, so do not increment new_value_dim_idx
            return value
        else:
            raise TypeError(
                "Only tiles can be indexed with subscript",
                node
            )

    def _parse_shape(self, node: ast.expr) -> List[ir.Expr]:
        """Parse shape expression (tuple of integers or single integer)."""
        if isinstance(node, ast.Tuple):
            dims = []
            for elt in node.elts:
                dims.append(self._resolve_expr(elt))
            return dims
        elif isinstance(node, ast.Constant):
            # Single dimension
            return [self._resolve_expr(node)]
        else:
            raise TypeError(
                "Shape must be tuple of integers or single integer",
                node
            )
        
 
    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------

    def _add_instruction(self, instr: ir.Instruction) -> None:
        """Add an instruction to the current instruction list."""
        self.current_instructions.append(instr)

    def _get_variable_info(self, name: str) -> SymbolInfo:
        """Get symbol info for a variable name."""
        info = self.symbol_table.lookup(name)
        if info is None:
            raise SymbolError(f"Undefined variable: {name}")
        return info

    def _resolve_expr(self, node: ast.expr) -> ir.Expr:
        """Convert an AST expression to an IR Expr."""
        if isinstance(node, ast.Constant):
            # Python numeric literal
            value = node.n
            if isinstance(value, int):
                return ir.ConstantExpr(ir.ConstantExprDataType.INT, value, loc=IRLoc(node))
            elif isinstance(value, float):
                return ir.ConstantExpr(ir.ConstantExprDataType.FLOAT, value, loc=IRLoc(node))
            elif isinstance(value, bool):
                return ir.ConstantExpr(ir.ConstantExprDataType.BOOL, value, loc=IRLoc(node))
            else:
                raise TypeError(f"Unsupported literal type: {type(value)}")

        elif isinstance(node, ast.Name):
            # Variable reference
            info = self._get_variable_info(node.id)
            if info.var_type != VarType.SCALAR and info.var_type != VarType.LOOP_VAR:
                raise TypeError(f"Expected scalar expression, got {node.id} (type={info.var_type})")
            if info.var_type == VarType.LOOP_VAR:
                # Loop variable
                return ir.LoopVarExpr(node.id, loc=IRLoc(node))
            else:
                if info.value is None:
                    raise SymbolError(f"Scalar variable {node.id} has no value")
                return info.value
        
        elif isinstance(node, ast.UnaryOp):
            # Unary operation
            operand = self._visit_expr(node.operand)
            if isinstance(node.op, ast.UAdd):
                return operand  # Unary plus
            elif isinstance(node.op, ast.USub):
                return ir.UnaryExpr(ir.UnaryExprOp.NEG, operand, loc=IRLoc(node))
            elif isinstance(node.op, ast.Not):
                return ir.UnaryExpr(ir.UnaryExprOp.NOT, operand, loc=IRLoc(node))
            else:
                raise UnsupportedFeatureError(f"Unsupported unary operator: {node.op.__class__.__name__}")

        elif isinstance(node, ast.BinOp):
            # Binary operation
            left = self._visit_expr(node.left)
            right = self._visit_expr(node.right)
            op = self._binop_to_BinaryExprOp(node.op)
            return ir.BinaryExpr(op, left, right, loc=IRLoc(node))

        elif isinstance(node, ast.BoolOp):
            # Boolean operation (and/or)
            values = [self._visit_expr(v) for v in node.values]
            if isinstance(node.op, ast.And):
                op = ir.BinaryExprOp.LOGICAL_AND
            elif isinstance(node.op, ast.Or):
                op = ir.BinaryExprOp.LOGICAL_OR
            else:
                raise UnsupportedFeatureError(f"Unsupported boolean operator: {node.op.__class__.__name__}")
            # Chain the operations
            result = values[0]
            for v in values[1:]:
                result = ir.BinaryExpr(op, result, v, loc=IRLoc(node))
            return result
        
        elif isinstance(node, ast.Compare):
            # Comparison operation
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise UnsupportedFeatureError("Chained comparisons are not supported")
            left = self._visit_expr(node.left)
            right = self._visit_expr(node.comparators[0])
            op_node = node.ops[0]
            swap_ab = False
            if isinstance(op_node, ast.Lt):
                op = ir.CompareExprOp.LE
            elif isinstance(op_node, ast.LtE):
                op = ir.CompareExprOp.LEQ
            elif isinstance(op_node, ast.Gt):
                op = ir.CompareExprOp.LE
                swap_ab = True
            elif isinstance(op_node, ast.GtE):
                op = ir.CompareExprOp.LEQ
                swap_ab = True
            elif isinstance(op_node, ast.Eq):
                op = ir.CompareExprOp.EQ
            elif isinstance(op_node, ast.NotEq):
                op = ir.CompareExprOp.NEQ
            else:
                raise UnsupportedFeatureError(f"Unsupported comparison operator: {op_node.__class__.__name__}")
            if swap_ab:
                left, right = right, left
            return ir.CompareExpr(op, left, right, loc=IRLoc(node))
        
        elif isinstance(node, ast.Call):
            # Function call (e.g., kdt.get_job_id())
            # We'll handle kdt.get_job_id specially
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'get_job_id':
                    # kdt.get_job_id() returns GetJobIdExpr
                    if node.args:
                        raise SyntaxError("kdt.get_job_id() takes no arguments")
                    return ir.GetJobIdExpr(loc=IRLoc(node))
            # Other calls handled by visit_Call
            raise SyntaxError(f"Unsupported function call in expression: {ast.dump(node)}")

        else:
            raise UnsupportedFeatureError(f"Unsupported expression type: {node.__class__.__name__}")

    @staticmethod
    def _binop_to_BinaryExprOp(op: ast.operator) -> ir.BinaryExprOp:
        """Convert AST operator to string."""
        if isinstance(op, ast.Add):
            return ir.BinaryExprOp.ADD
        elif isinstance(op, ast.Sub):
            return ir.BinaryExprOp.SUB
        elif isinstance(op, ast.Mult):
            return ir.BinaryExprOp.MUL
        elif isinstance(op, ast.FloorDiv):
            return ir.BinaryExprOp.FLOOR_DIV
        elif isinstance(op, ast.Div):
            return ir.BinaryExprOp.DIV
        elif isinstance(op, ast.Mod):
            return ir.BinaryExprOp.MOD
        elif isinstance(op, ast.BitAnd):
            return ir.BinaryExprOp.BITWISE_AND
        elif isinstance(op, ast.BitOr):
            return ir.BinaryExprOp.BITWISE_OR
        elif isinstance(op, ast.BitXor):
            return ir.BinaryExprOp.BITWISE_XOR
        elif isinstance(op, ast.And):
            return ir.BinaryExprOp.LOGICAL_AND
        elif isinstance(op, ast.Or):
            return ir.BinaryExprOp.LOGICAL_OR
        elif isinstance(op, ast.LShift):
            return ir.BinaryExprOp.LSHIFT
        elif isinstance(op, ast.RShift):
            return ir.BinaryExprOp.RSHIFT
        else:
            raise UnsupportedFeatureError(f"Unsupported binary operator: {op.__class__.__name__}")

    def _parse_func_call_args(self, node: ast.Call, signature: List[FuncArg]) -> Dict[str, Union[int, float, bool, ast.expr, ir.Tile, ir.Expr]]:
        """
        Fit positional and keyword arguments to a function signature.
        If `signature.interpret_as` is not None, then interpret it and perform best-effort type checking
        Returns a dictionary mapping parameter names to argument values.
        """
        def interpret_as(node: ast.expr, interpret_as: InterpretOptions):
            if interpret_as == InterpretOptions.NONE:
                return node
            elif interpret_as in [InterpretOptions.TILE, InterpretOptions.EXPR]:
                res = self._visit_expr(node)
                if not isinstance(res, ir.Tile if interpret_as == InterpretOptions.TILE else ir.Expr):
                    raise TypeError(f"Expect argument to have type {interpret_as}, but found {type(res)}: {res}")
                return res
            elif interpret_as in [InterpretOptions.CONST, InterpretOptions.CONST_INT, InterpretOptions.CONST_FLOAT, InterpretOptions.CONST_BOOL]:
                res = self._resolve_expr(node)
                const = res.as_constant()
                if const is None:
                    raise ConstantRequiredError(f"Expect argument to be a compile-time constant, but found: {res}")
                dtype_map = {
                    InterpretOptions.CONST_INT: int,
                    InterpretOptions.CONST_FLOAT: float,
                    InterpretOptions.CONST_BOOL: bool,
                }
                if interpret_as in dtype_map:
                    const = dtype_map[interpret_as](const)
                return const
            elif interpret_as == InterpretOptions.STRING:
                res = ast.literal_eval(node)
                if not isinstance(res, str):
                    raise TypeError(f"Expect argument to be a string, but found: {type(res)}: {res}")
                return res
            else:
                raise InternalError(f"Unknown interpret_as: {interpret_as}")

        assert isinstance(node, ast.Call)
        fitted_args = {}
        # Assign positional arguments
        for i, arg in enumerate(node.args):
            if i >= len(signature):
                raise TypeError("Too many positional arguments")
            fitted_args[signature[i].name] = interpret_as(arg, signature[i].interpret_as)
        # Assign keyword arguments
        signature_as_dict = {x.name: x for x in signature}
        for keyword_arg in node.keywords:
            key = keyword_arg.arg
            if key not in signature_as_dict:
                raise TypeError(f"Unexpected keyword argument: {key}")
            if key in fitted_args:
                raise TypeError(f"Multiple values for argument: {key}")
            fitted_args[key] = interpret_as(keyword_arg.value, signature_as_dict[key].interpret_as)
        # Check for missing arguments
        for arg in signature:
            if arg.name not in fitted_args:
                if arg.default_val is None:
                    raise TypeError(f"Missing argument: {arg.name}")
                else:
                    fitted_args[arg.name] = arg.default_val
        return fitted_args

    def generic_visit(self, node: ast.AST) -> Any:
        """Called for nodes without specific visitor methods."""
        raise UnsupportedFeatureError(f"Unsupported Python construct: {node.__class__.__name__}")
