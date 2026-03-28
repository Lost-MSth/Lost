"""
Compilation error classes for the KDT-DSL frontend compiler.
"""

from typing import Optional
import ast


class CompilationError(Exception):
    """Base class for all compilation errors."""
    def __init__(self, message: str, node: Optional[ast.AST]=None, ast_start_lineno: Optional[int]=None):
        super().__init__(message)
        self.message = message
        self.node = node
        self.ast_start_lineno = ast_start_lineno

    def __str__(self) -> str:
        lineno = getattr(self.node, 'lineno', None)
        col_offset = getattr(self.node, 'col_offset', None)
        msg = ''
        if lineno is not None:
            msg += f"Line {self.ast_start_lineno+lineno}, "
        if col_offset is not None:
            msg += f"Col {col_offset}, "
        return msg + self.message


class TypeError(CompilationError):
    """Type error during compilation."""
    pass


class ShapeError(CompilationError):
    """Shape error during compilation."""
    pass

class IndexError(CompilationError):
    """Internal error in the compiler"""
    pass

class SemanticError(CompilationError):
    """Semantic error (e.g., alloc_spm in loop)."""
    pass


class SyntaxError(CompilationError):
    """KDT-DSL syntax error."""
    pass


class SymbolError(CompilationError):
    """Undefined symbol or duplicate definition."""
    pass


class ConstantRequiredError(CompilationError):
    """A constant expression was required but not provided."""
    pass


class UnsupportedFeatureError(CompilationError):
    """Unsupported Python feature in KDT-DSL."""
    pass

class InternalError(CompilationError):
    """Internal error in the compiler"""
    pass

class IRException(CompilationError):
    """Exception raised for IR errors in the KDT judge system."""
    pass
