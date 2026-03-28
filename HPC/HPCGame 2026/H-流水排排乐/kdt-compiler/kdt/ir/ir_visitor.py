import abc
from typing import Any
from kdt.ir import *

class IRVisitor(abc.ABC):
    """
    Base class for visitors that traverse the KDT-DSL IR tree.

    Subclasses should implement visit methods for each concrete IR node type.
    """

    # Expressions
    def visit_ConstantExpr(self, node: ConstantExpr) -> Any:
        pass

    def visit_GetJobIdExpr(self, node: GetJobIdExpr) -> Any:
        pass

    def visit_LoopVarExpr(self, node: LoopVarExpr) -> Any:
        pass

    def visit_UnaryExpr(self, node: UnaryExpr) -> Any:
        pass

    def visit_BinaryExpr(self, node: BinaryExpr) -> Any:
        pass

    def visit_CompareExpr(self, node: CompareExpr) -> Any:
        pass
    
    # Tiles
    def visit_TileStorage(self, node: TileStorage) -> Any:
        pass

    def visit_Tile(self, node: Tile) -> Any:
        pass
    
    # Instructions
    def visit_Unary(self, node: Unary) -> Any:
        pass

    def visit_Binary(self, node: Binary) -> Any:
        pass

    def visit_Compare(self, node: Compare) -> Any:
        pass

    def visit_MatMul(self, node: MatMul) -> Any:
        pass

    def visit_FMA(self, node: FMA) -> Any:
        pass

    def visit_Reduce(self, node: Reduce) -> Any:
        pass

    def visit_Where(self, node: Where) -> Any:
        pass

    def visit_Copy(self, node: Copy) -> Any:
        pass

    def visit_Fill(self, node: Fill) -> Any:
        pass

    def visit_Load(self, node: Load) -> Any:
        pass

    def visit_Store(self, node: Store) -> Any:
        pass

    def visit_Print(self, node: Print) -> Any:
        pass

    # Program structure
    def visit_Block(self, node: Block) -> Any:
        pass

    def visit_ForLoop(self, node: ForLoop) -> Any:
        pass

    def visit_IfElse(self, node: IfElse) -> Any:
        pass

    def visit_Kernel(self, node: Kernel) -> Any:
        pass


class AutoRecursiveIRVisitor(IRVisitor):
    """
    An IR visitor that automatically recurses into child nodes.

    Subclasses can override specific visit methods to add custom behavior.
    """

    # Expressions
    def visit_ConstantExpr(self, node: ConstantExpr) -> Any:
        pass

    def visit_GetJobIdExpr(self, node: GetJobIdExpr) -> Any:
        pass

    def visit_LoopVarExpr(self, node: LoopVarExpr) -> Any:
        pass

    def visit_UnaryExpr(self, node: UnaryExpr) -> Any:
        node.operand.accept(self)
        
    def visit_BinaryExpr(self, node: BinaryExpr) -> Any:
        node.left.accept(self)
        node.right.accept(self)

    def visit_CompareExpr(self, node: CompareExpr) -> Any:
        node.left.accept(self)
        node.right.accept(self)

    # Tiles
    def visit_TileStorage(self, node: TileStorage) -> Any:
        pass

    def visit_Tile(self, node: Tile) -> Any:
        node.storage.accept(self)

    # Instructions
    def visit_Unary(self, node: Unary) -> Any:
        node.x.accept(self)
        node.out.accept(self)

    def visit_Binary(self, node: Binary) -> Any:
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)

    def visit_Compare(self, node: Compare) -> Any:
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)

    def visit_MatMul(self, node: MatMul) -> Any:
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)
        node.accumulate.accept(self)

    def visit_FMA(self, node: FMA) -> Any:
        node.a.accept(self)
        node.b.accept(self)
        node.c.accept(self)
        node.out.accept(self)

    def visit_Reduce(self, node: Reduce) -> Any:
        node.src.accept(self)
        node.out.accept(self)

    def visit_Where(self, node: Where) -> Any:
        node.cond.accept(self)
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)

    def visit_Copy(self, node: Copy) -> Any:
        node.src.accept(self)
        node.dst.accept(self)
        
    def visit_Fill(self, node: Fill) -> Any:
        node.out.accept(self)

    def visit_Load(self, node: Load) -> Any:
        node.src.accept(self)
        node.dst.accept(self)

    def visit_Store(self, node: Store) -> Any:
        node.src.accept(self)
        node.dst.accept(self)

    def visit_Print(self, node: Print) -> Any:
        node.tile.accept(self)

    # Program structure
    def visit_Block(self, node: Block) -> Any:
        for instr in node.instructions:
            instr.accept(self)

    def visit_ForLoop(self, node: ForLoop) -> Any:
        node.body.accept(self)

    def visit_IfElse(self, node: IfElse) -> Any:
        node.condition.accept(self)
        node.then_body.accept(self)
        if node.else_body:
            node.else_body.accept(self)

    def visit_Kernel(self, node: Kernel) -> Any:
        node.body.accept(self)
        