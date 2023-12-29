from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types.type as ct

class BoolType(ct.CompilerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 1
        self.value = ir.IntType(1)
        self.name = "bool"
        self.ptr_count = 0

    

