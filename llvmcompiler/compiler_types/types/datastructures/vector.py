from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types.type as ct
import llvmcompiler.llvmlite_custom as llc

# Vector
class VectorType(ct.CompilerType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type
        self._size = self.type.size * self.count
        self.value = llc.ScaleableVectorType(self.type.value, self.count)

    def get_type(self):
        return self.type

    def cast_ptr(self):
        return VectorPointerType(self.type, self.count)
    
class VectorPointerType(VectorType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type
        self._size = self.type.size * self.count
        self.value = llc.ScaleableVectorType(self.type.value, self.count).as_pointer()