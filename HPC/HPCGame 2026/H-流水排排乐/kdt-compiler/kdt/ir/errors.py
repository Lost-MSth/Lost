"""
runtime error classes for the KDT-DSL frontend compiler.
"""

from typing import Optional
from .ir import IRLoc

class RuntimeError(Exception):
    """Base class for all runtime errors."""
    def __init__(self, message: str, loc: Optional[IRLoc]=None, ast_start_lineno: Optional[int]=None):
        super().__init__(message)
        self.message = message
        self.loc = loc
        self.ast_start_lineno = ast_start_lineno

    def __str__(self) -> str:
        lineno = getattr(self.loc, 'lineno', None)
        col_offset = getattr(self.loc, 'col_offset', None)
        msg = ''
        if lineno is not None:
            msg += f"Line {self.ast_start_lineno+lineno}, "
        if col_offset is not None:
            msg += f"Col {col_offset}, "
        return msg + self.message


class TypeError(RuntimeError):
    """Type error during runtime."""
    pass


class ShapeError(RuntimeError):
    """Shape error during runtime."""
    pass


class ValueError(RuntimeError):
    """Value error during runtime."""
    pass


class SemanticError(RuntimeError):
    """Semantic error (e.g., alloc_spm in loop)."""
    pass


class SyntaxError(RuntimeError):
    """KDT-DSL syntax error."""
    pass


class SymbolError(RuntimeError):
    """Undefined symbol or duplicate definition."""
    pass


class ConstantRequiredError(RuntimeError):
    """A constant expression was required but not provided."""
    pass


class UnsupportedFeatureError(RuntimeError):
    """Unsupported Python feature in KDT-DSL."""
    pass

class InternalError(RuntimeError):
    """Internal error in the compiler"""
    pass
