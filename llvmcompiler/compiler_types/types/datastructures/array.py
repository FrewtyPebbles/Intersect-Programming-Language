from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct

# Array
class ArrayType(ct.CompilerType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type
        self._parent = None
        self.module = None

    @property    
    def size(self):
        self.type.parent = self.parent
        self.type.module = self.module
        return self.type.size * self.count
        
    @property
    def value(self):
        self.type.parent = self.parent
        self.type.module = self.module
        return ir.ArrayType(self.type.value, self.count)

    @property
    def parent(self):
        return self._parent
    
    @parent.setter
    def parent(self, val):
        self.type.parent = self._parent
        self.type.module = self.module
        self._parent = val


    def get_type(self):
        return self.type

    def cast_ptr(self):
        return ArrayPointerType(self.type, self.count)
    
class ArrayPointerType(ArrayType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type
        self._parent = None
        self.module = None
    
    @property
    def value(self):
        self.type.parent = self.parent
        self.type.module = self.module
        return ir.ArrayType(self.type.value, self.count).as_pointer()