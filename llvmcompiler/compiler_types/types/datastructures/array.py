from copy import deepcopy
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct

# Array
class ArrayType(ct.CompilerType):
    def __init__(self, item_type:ct.CompilerType, count:int, ptr_count = 0) -> None:
        self.count = count
        self.type = item_type
        self._parent = None
        self.module = None
        self._size = None
        self._value = None
        self.ptr_count = ptr_count

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
        for pn in range(self.ptr_count):
            self._value = self._value.as_pointer()
        return self._value
    
    @value.setter
    def value(self, val):
        if self._value == None:
            self.type.parent = self.parent
            self.type.module = self.module
        self._value = val

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
        self.ptr_count += 1
        return self

    def create_deref(self):
        self_cpy = deepcopy(self)
        self_cpy.ptr_count -= 1
        return self_cpy

    def __repr__(self) -> str:
        return f"{'$' * self.ptr_count}[{self.type} x {self.count}]"
    
class ArrayPointerType(ArrayType):
    def __init__(self, item_type:ct.CompilerType, count:int, ptr_count = 0) -> None:
        self.count = count
        self.type = item_type
        self._parent = None
        self.module = None
        self.ptr_count = ptr_count
    
    @property
    def value(self):
        self.type.parent = self.parent
        self.type.module = self.module
        val = ir.ArrayType(self.type.value, self.count)
        for _ in range(self.ptr_count):
            val = val.as_pointer()
        return val