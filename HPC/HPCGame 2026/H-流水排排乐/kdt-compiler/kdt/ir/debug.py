from kdt.ir.ir_visitor import IRVisitor
from kdt.ir import *

class IRPrintor(IRVisitor):
    """IR visitor that prints the IR nodes for debugging purposes."""

    def __init__(self, recursive_into_tiles: bool = False):
        self.indent_level = 0
        self.recursive_into_tiles = recursive_into_tiles

    def _print(self, *args, **kwargs):
        print("    " * self.indent_level, end="")
        print(*args, **kwargs)
    
    def visit_ConstantExpr(self, node: ConstantExpr):
        self._print(str(node))
    
    def visit_GetJobIDExpr(self, node: GetJobIdExpr):
        self._print(str(node))
    
    def visit_LoopVarExpr(self, node: LoopVarExpr):
        self._print(str(node))
        
    def visit_UnaryExpr(self, node: UnaryExpr):
        self._print(str(node))
        self.indent_level += 1
        node.operand.accept(self)
        self.indent_level -= 1
        
    def visit_BinaryExpr(self, node: BinaryExpr):
        self._print(str(node))
        self.indent_level += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent_level -= 1
    
    def visit_CompareExpr(self, node: CompareExpr):
        self._print(str(node))
        self.indent_level += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent_level -= 1
        
    def visit_TileStorage(self, node: TileStorage):
        self._print(str(node))

    def visit_Tile(self, node: Tile):
        if not self.recursive_into_tiles:
            return
        self._print(str(node))
        self.indent_level += 1
        node.storage.accept(self)
        self.indent_level -= 1

    def visit_Unary(self, node: Unary):
        self._print(str(node))
        self.indent_level += 1
        node.x.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Binary(self, node: Binary):
        self._print(str(node))
        self.indent_level += 1
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Compare(self, node: Compare):
        self._print(str(node))
        self.indent_level += 1
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_MatMul(self, node: MatMul):
        self._print(str(node))
        self.indent_level += 1
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)
        node.accumulate.accept(self)
        self.indent_level -= 1
    
    def visit_FMA(self, node: FMA):
        self._print(str(node))
        self.indent_level += 1
        node.a.accept(self)
        node.b.accept(self)
        node.c.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Reduce(self, node: Reduce):
        self._print(str(node))
        self.indent_level += 1
        node.src.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Where(self, node: Where):
        self._print(str(node))
        self.indent_level += 1
        node.cond.accept(self)
        node.a.accept(self)
        node.b.accept(self)
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Copy(self, node: Copy):
        self._print(str(node))
        self.indent_level += 1
        node.src.accept(self)
        node.dst.accept(self)
        self.indent_level -= 1
        
    def visit_Fill(self, node: Fill):
        self._print(str(node))
        self.indent_level += 1
        node.out.accept(self)
        self.indent_level -= 1
    
    def visit_Load(self, node: Load):
        self._print(str(node))
        self.indent_level += 1
        node.src.accept(self)
        node.dst.accept(self)
        self.indent_level -= 1
    
    def visit_Store(self, node: Store):
        self._print(str(node))
        self.indent_level += 1
        node.src.accept(self)
        node.dst.accept(self)
        self.indent_level -= 1
    
    def visit_Print(self, node: Print):
        self._print(str(node))
        self.indent_level += 1
        node.tile.accept(self)
        self.indent_level -= 1
    
    def visit_Block(self, node: Block):
        self._print(str(node))
        self.indent_level += 1
        for instr in node.instructions:
            instr.accept(self)
        self.indent_level -= 1

    def visit_ForLoop(self, node: ForLoop):
        self._print(str(node))
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1

    def visit_IfElse(self, node: IfElse):
        self._print(str(node))
        self.indent_level += 1
        node.condition.accept(self)
        node.then_body.accept(self)
        if node.else_body:
            node.else_body.accept(self)
        self.indent_level -= 1
        
    def visit_Kernel(self, node: Kernel):
        self._print(str(node))
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        
        
def print_ir(ir_node: IRNode):
    printer = IRPrintor()
    ir_node.accept(printer)
