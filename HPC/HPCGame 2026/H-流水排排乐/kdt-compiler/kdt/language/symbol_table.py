"""
Symbol table for tracking variables and their metadata during compilation.
"""

from typing import Dict, Optional, List, Union
from enum import Enum

from kdt.ir import DataType, MemorySpace, Shape, TileStorage, Tile, Expr
from kdt.language.errors import SymbolError


class VarType(Enum):
    """Variable type classification."""
    TILE = "tile"
    SCALAR = "scalar"
    LOOP_VAR = "loop_var"  # Special scalar used as loop variable
    DICT = "dict"   # Only for task_args (whose elements are int scalars) or io_tensors (whose elements are tiles)


class SymbolInfo:
    """Metadata for a variable symbol."""
    def __init__(
        self,
        name: str,  # Variable name
        var_type: VarType,  # Variable type
        dtype: Optional[DataType] = None,
        memory_space: Optional[MemorySpace] = None, # Only for tiles
        shape: Optional[Shape] = None,  # Only for tiles
        value: Optional[Expr] = None,   # Only for scalars
        tile_view: Optional[Tile] = None,
        storage: Optional[TileStorage] = None,
        data: Optional[Dict[str, Union[int, Tile]]] = None
    ):
        self.name = name
        self.var_type = var_type
        self.dtype = dtype
        self.memory_space = memory_space
        self.shape = shape
        self.value = value
        self.tile_view = tile_view
        self.storage = storage
        self.data = data

    def __repr__(self) -> str:
        parts = [self.name, self.var_type.value]
        if self.dtype:
            parts.append(f"dtype={self.dtype.value}")
        if self.memory_space:
            parts.append(f"space={self.memory_space.value}")
        if self.shape:
            parts.append(f"shape={self.shape}")
        if self.value:
            parts.append(f"value={self.value}")
        if self.tile_view:
            parts.append(f"tile_view={self.tile_view}")
        if self.storage:
            parts.append(f"storage={self.storage}")
        if self.data:
            parts.append(f"data={self.data}")
        return f"SymbolInfo({', '.join(parts)})"


class Scope:
    """
    A scope containing symbol definitions.
    Scope can have a parent scope for nested lookups.
    """
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent = parent
        self.symbols: Dict[str, SymbolInfo] = {}

    def define(self, name: str, info: SymbolInfo) -> None:
        """Define a new symbol in this scope."""
        if name in self.symbols:
            raise SymbolError(f"Symbol '{name}' already defined in this scope")
        self.symbols[name] = info

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """Look up a symbol in this scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

class SymbolTable:
    """Manages nested scopes during compilation."""
    def __init__(self):
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]

    def push_scope(self) -> None:
        """Push a new inner scope."""
        new_scope = Scope(self.current_scope)
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope

    def pop_scope(self) -> None:
        """Pop the current scope."""
        if len(self.scope_stack) <= 1:
            raise RuntimeError("Cannot pop the global scope")
        self.scope_stack.pop()
        self.current_scope = self.scope_stack[-1]

    def define(self, name: str, info: SymbolInfo) -> None:
        """Define a symbol in the current scope."""
        self.current_scope.define(name, info)

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """Look up a symbol from the current scope outward."""
        return self.current_scope.lookup(name)
