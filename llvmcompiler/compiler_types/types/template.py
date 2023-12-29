from __future__ import annotations
from copy import deepcopy
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct

if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.struct as st
    import llvmcompiler.ir_renderers.function as fn


# I32
class Template(ct.CompilerType):
    
    def __init__(self, name = "", parent: fn.Function | st.Struct = None, ptr_count = 0) -> None:
        self.name = name
        self._value = None
        self.parent: fn.Function | st.Struct = parent
        self._size = None
        self._count = None
        self.ptr_count = ptr_count

    def __hash__(self) -> int:
        return hash(f"{self.name}{self._value}{self.ptr_count}")
    

    def get_template_type(self):
        return self.parent.get_template_type(self.name)

    @property
    def value(self):
        self._value = self.get_template_type().value
        for _ in range(self.ptr_count):
            self._value = self._value.as_pointer()
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = value
    
    
    @property
    def size(self):

        return self.get_template_type().size
        
    
    @property
    def count(self):
        return self.get_template_type().count


    def __eq__(self, __value: Template | str) -> bool:
        if isinstance(__value, Template):
            return self.value == __value.value
        else:
            return self.value == __value
    
    def __repr__(self) -> str:
        return f"{'$'*self.ptr_count}{self.name}"
    