from __future__ import annotations
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct
if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.struct as st
    import llvmcompiler.ir_renderers.function as fn

# I32
class Template(ct.CompilerType):
    
    def __init__(self, name = "", parent: fn.Function | st.Struct = None) -> None:
        self.name = name
        self._value = None
        self.parent: fn.Function | st.Struct = parent

    def get_template_type(self):
        return self.parent.get_template_type(self.name)

    @property
    def value(self):
        return self.get_template_type().value
    
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
        
    def cast_ptr(self):
        ptr = TemplatePointer(self.name, self.parent)
        return ptr
    
    def __repr__(self) -> str:
        return f"(Template : {self.name})"
    

class TemplatePointer(Template):
    
    def get_template_type(self):
        return super().get_template_type().cast_ptr()
    
    def __repr__(self) -> str:
        return f"(TemplatePTR : {self.name})"