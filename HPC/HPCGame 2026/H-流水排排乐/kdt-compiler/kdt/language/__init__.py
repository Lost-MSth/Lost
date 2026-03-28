"""
KDT-DSL language frontend compiler.

This module provides the frontend compiler that transforms Python-written KDT-DSL kernels into KDT-DSL IR.
"""

# Public API
from kdt.language.frontend import kernel, KernelFunction, CompiledKernel
from kdt.language.launch import launch_kernel

from kdt.language.frontend import FrontendCompiler
from kdt.language.ast_visitor import ASTVisitor
from kdt.language.symbol_table import SymbolTable, SymbolInfo, VarType
from kdt.language.errors import (
    CompilationError, TypeError, ShapeError, SemanticError,
    SyntaxError, SymbolError, ConstantRequiredError, UnsupportedFeatureError
)

__all__ = [
    # Public API
    'kernel',
    'KernelFunction',
    'launch_kernel',
    # Compiler components
    'FrontendCompiler',
    'ASTVisitor',
    'SymbolTable',
    'SymbolInfo',
    'VarType',
    # Error classes
    'CompilationError',
    'TypeError',
    'ShapeError',
    'SemanticError',
    'SyntaxError',
    'SymbolError',
    'ConstantRequiredError',
    'UnsupportedFeatureError',
]