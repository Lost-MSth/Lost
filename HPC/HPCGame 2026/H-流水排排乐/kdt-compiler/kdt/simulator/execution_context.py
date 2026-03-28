"""
ExecutionContext for KDT-DSL simulator.
"""

from typing import Dict, List, Tuple
import enum
import dataclasses
import numpy as np
from kdt.ir import TileStorage, Tile, MemorySpace, DataType
import math

class TileStorageState:
    """
    The state of a TileStorage during execution.

    Including:
        storage: The TileStorage object
        array: The NumPy array backing the storage
        read_release_time: The cycle when the last read is released (so that it's safe to write)
        write_release_time: The cycle when the last write is released (so that it's safe to read)
    """
    def __init__(self, storage: TileStorage, array: np.ndarray):
        self.storage = storage
        self.array = array
        self.read_release_time = np.zeros_like(array, dtype=np.int64)
        self.write_release_time = np.zeros_like(array, dtype=np.int64)

class ExecutionContext:
    """
    Execution context for a single job.

    Attributes:
        job_id: Current job ID (0 to num_jobs-1)
        start_lineno: The starting line number of the kernel in source code
        loop_vars: Dictionary mapping loop variable names to current values
        global_storage: Dictionary mapping global TileStorage objects to their NumPy arrays
        spm_storage: Dictionary mapping SPM TileStorage objects to their NumPy arrays
        nxt_isu_issue_cycle: The next cycle when ISU can issue an instruction
    """

    def __init__(self, job_id: int, start_lineno: int):
        self.job_id = job_id
        self.start_lineno = start_lineno
        self.loop_vars: Dict[str, int] = {}
        self.global_storage: Dict[TileStorage, TileStorageState] = {}
        self.spm_storage: Dict[TileStorage, TileStorageState] = {}
        self.allocated_spm_size = 0 # Track the allocated size in SPM (in bytes)
        self.nxt_isu_issue_cycle = 1

    def allocate_global_storage(self, storage: TileStorage, array: np.ndarray):
        """
        Assign NumPy array for a global TileStorage.
        """
        if storage.space != MemorySpace.GLOBAL:
            raise ValueError(f"Cannot allocate global storage for non-global tile: {storage}")
        self.global_storage[storage] = TileStorageState(storage, array)

    def allocate_spm_storage(self, storage: TileStorage) -> np.ndarray:
        """
        Allocate NumPy array for an SPM TileStorage.
        """
        if storage.space != MemorySpace.SPM:
            raise ValueError(f"Cannot allocate SPM storage for non-SPM tile: {storage}")

        size = np.prod(storage.shape)

        if storage.dtype == DataType.FLOAT32:
            dtype = np.float32
            self.allocated_spm_size += size * 4
        elif storage.dtype == DataType.BOOL:
            dtype = np.bool_
            self.allocated_spm_size += math.ceil(size / 8)
        else:
            raise ValueError(f"Unsupported dtype: {storage.dtype}")

        array = np.zeros(storage.shape, dtype=dtype)    # For safety, we initialize with zeros
        self.spm_storage[storage] = TileStorageState(storage, array)
        return array

    def get_global_array(self, storage: TileStorage) -> TileStorageState:
        """
        Get NumPy array for global TileStorage.

        Raises KeyError if storage not allocated.
        """
        return self.global_storage[storage]
    
    def get_spm_array(self, storage: TileStorage) -> TileStorageState:
        """
        Get NumPy array for SPM TileStorage.

        Raises KeyError if storage not allocated.
        """
        return self.spm_storage[storage]
    
    def get_nxt_isu_issue_cycle(self) -> int:
        """Get the next ISU issue cycle."""
        return self.nxt_isu_issue_cycle

    def advance_nxt_isu_issue_cycle(self):
        """Advance the next ISU issue cycle by 1."""
        self.nxt_isu_issue_cycle += 1

    def set_loop_var(self, name: str, value: int):
        """Set a loop variable value."""
        self.loop_vars[name] = value

    def get_loop_var(self, name: str) -> int:
        """Get a loop variable value."""
        return self.loop_vars[name]

    def clear_loop_var(self, name: str):
        """Remove a loop variable from context."""
        if name in self.loop_vars:
            del self.loop_vars[name]