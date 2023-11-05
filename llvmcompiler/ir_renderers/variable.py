from __future__ import annotations

from llvmlite import ir

from llvmcompiler.compiler_types.type import is_ptr
from ..compiler_types import ScalarType, AnyType, DataStructureType
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .builder_data import BuilderData

class Variable:
    def __init__(self, builder:BuilderData, name:str, value:Value):
        self.builder = builder
        self.name = name
        self.value = value
        self.type = self.value.type

        # declare the variable
        self.variable = self.builder.cursor.alloca(self.type.value, name = self.name)

        if self.value.value != None:
            self.set(self.value)
            
    def set(self, value:Union[Variable, Value, any]):
        if isinstance(value, Variable):
            self.builder.cursor.store(value.load(), self.variable)
        elif isinstance(value, Value):
            self.builder.cursor.store(value.get_value(), self.variable)
        else:
            # this is for storing llvm instruction results in the variable
            self.builder.set_variable(self.name, value)

    def load(self):
        return self.builder.cursor.load(self.variable)
    
    def is_ptr(self) -> bool:
        return is_ptr(self.type)
    
class Value:
    def __init__(self, builder:BuilderData, value_type:AnyType, raw_value:Union[str, any] = None) -> None:
        self.builder = builder
        self.type = value_type
        self.value = raw_value
        if isinstance(self.value, str):
            # add a null terminator if it is a string
            self.value = f"{self.value}\00"
        # TODO: process raw_value into python value then set self.value = to the processed value


    def get_value(self):
        if isinstance(self.type, DataStructureType):
            if self.type.type == ScalarType.c8:
                return ir.Constant(self.type.value, bytearray(self.value.encode()))
        return self.type.value(self.value)
    
    def write(self) -> ir.AllocaInstr:
        const = self.get_value()
        ret_val = self.builder.cursor.alloca(const.type)
        self.builder.cursor.store(const, ret_val)
        return ret_val
    
    def dbg_print(self):
        print(self.type.value)

