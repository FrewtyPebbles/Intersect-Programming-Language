from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types.type as ct


# I32
class IntegerType(ct.CompilerType):
    """
    This is where integer specific type methods are added.
    """
    def __init__(self, size:int, name = "i") -> None:
        self.count = 1
        self._size = size
        self.value = ir.IntType(self._size)
        self.name = name
        self.ptr_count = 0


    
    

class I32Type(IntegerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 32
        self.value = ir.IntType(self._size)
        self.name = "i32"
        self.ptr_count = 0

    

class I8Type(IntegerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 8
        self.value = ir.IntType(self._size)
        self.name = "i8"
        self.ptr_count = 0

    

class I64Type(IntegerType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 64
        self.value = ir.IntType(self._size)
        self.name = "i64"
        self.ptr_count = 0



    
