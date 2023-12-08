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
        self._size = None
        self._value = None

    @property    
    def size(self):
        if self._size == None:
            self.type.parent = self.parent
            self.type.module = self.module
            self._size = self.type.size * self.count
        return self._size
        
    @property
    def value(self):
        if self._value == None:
            self.type.parent = self.parent
            self.type.module = self.module
            self._value = ir.ArrayType(self.type.value, self.count)
        return self._value

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