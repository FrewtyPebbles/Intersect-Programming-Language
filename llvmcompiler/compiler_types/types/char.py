from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types.type as ct

# I32
class C8Type(ct.CompilerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 8
        self.value = ir.IntType(8)
        self.name = "c8"

    def cast_ptr(self):
        return C8PointerType()
    
class C8PointerType(ct.CompilerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 8
        self.value = ir.IntType(8).as_pointer()
        self.name = "c8"