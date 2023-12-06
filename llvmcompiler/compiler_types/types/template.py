from __future__ import annotations
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct

if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.struct as st
    import llvmcompiler.ir_renderers.function as fn

from copy import deepcopy

# I32
class Template(ct.CompilerType):
    
    def __init__(self, name = "", parent: fn.Function | st.Struct = None) -> None:
        self.name = name
        self._value = None
        self.parent: fn.Function | st.Struct = parent

    def get_template_type(self):
        return deepcopy(self.parent.get_template_type(self.name))

    @property
    def value(self):
        if self._value == None:
            self._value = self.get_template_type().value
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
            return self._value == __value.value
        else:
            return self._value == __value
    
    def __repr__(self) -> str:
        return f"(Template : {self.name})"
    
class TemplatePointer(Template):
    
    def __init__(self, name="", parent: fn.Function | st.Struct = None, ptr_count = 0) -> None:
        super().__init__(name, parent)
        self.ptr_count = ptr_count
    
    def get_template_type(self):
        ptr = super().get_template_type()
        return ptr
    
    @property
    def value(self):
        if self._value == None:
            self._value = deepcopy(self.get_template_type().value)
            for _ in range(self.ptr_count):
                self._value = self._value.as_pointer()
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = value

    def __repr__(self) -> str:
        return f"(TemplatePTR : {{{self.name}, {self.ptr_count}}})"