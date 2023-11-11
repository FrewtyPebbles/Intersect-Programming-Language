from __future__ import annotations
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.variable as vari
from llvmlite import ir


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import llvmcompiler.modules as md
    

class Struct(ct.CompilerType):
    """
    When the syntax tree builder checks the namespace against lables, it should check the struct namespace first.
    """
    _size:int
    value:ir.IdentifiedStructType
    module: md.Module
    def __init__(self, name:str, attributes:dict[str, ct.CompilerType] = {}, packed = False) -> None:
        self.name = name
        self.raw_attributes = attributes
        # the attributes are key value pairs that contain the attribute indexes
        self.attributes:dict[str, vari.Value] = {}
        self.functions:dict[str, ir.Function] = {
            #these are functions that are on this struct type
        }
        self.packed = packed
        self._size = 0
        self.module = None

    def get_attribute(self, attribute:str):
        return self.attributes[attribute]

    def write(self):
        self.value = self.module.module.context.get_identified_type(self.name)
        types = []
        for at_type_ind, (at_key, at_type) in enumerate(self.raw_attributes.items()):
            self.attributes[at_key] = vari.Value(ct.I32Type(), at_type_ind)
            self._size += at_type.size
            types.append(at_type.value)
        self.value.packed = self.packed
        self.value.set_body(*types)
        

