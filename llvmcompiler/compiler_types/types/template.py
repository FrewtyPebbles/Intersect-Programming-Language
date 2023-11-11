from __future__ import annotations
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.function as fn

# I32
class Template(ct.CompilerType):
    
    def __init__(self, name = "") -> None:
        self.count = 1
        self._size = 8
        self.name = name
        self.parent: fn.Function | ct.Struct = None

    @property
    def value(self):
        return self.parent.get_template_type(self.name)


    def __eq__(self, __value: Template | str) -> bool:
        if isinstance(__value, Template):
            return self.value == __value.value
        else:
            return self.value == __value