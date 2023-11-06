from __future__ import annotations

from llvmlite import ir

from llvmcompiler.compiler_types.type import is_ptr
import llvmcompiler.ir_renderers.operation as op
from ..compiler_types import ScalarType, AnyType, DataStructureType
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .builder_data import BuilderData
import llvmcompiler.ir_renderers.builder_data as bd

class Variable:
    def __init__(self, builder:BuilderData, name:str, value:Union[Variable, Value, any], heap = False):
        self.builder = builder
        self.name = name
        self.value = value
        self.heap = heap #wether a variable is stored on the heap or not
        self.type = self.value.type.cast_ptr() if self.heap else self.value.type

        # declare the variable
        if self.heap:
            malloc_call = self.builder.cursor.call(self.builder.functions["allocate"], [bd.SIZE_T(self.value.type.size)])

            bc = self.builder.cursor.bitcast(malloc_call, self.type.value)

            self.variable = self.builder.cursor.gep(bc, [ir.IntType(32)(0)], inbounds=True, name = self.name)
            
        else:
            self.variable = self.builder.cursor.alloca(self.type.value, name = self.name)

        self.builder.declare_variable(self)

        if self.value.value != None:
            self.set(self.value)
            
    def set(self, value:Union[Variable, Value, any]):
        self.builder.set_variable(self, value)

    def load(self):
        return self.builder.cursor.load(self.variable)
    
    @property
    def is_pointer(self):
        return self.type.value.is_pointer
    
class Value:
    def __init__(self, builder:BuilderData, value_type:AnyType, raw_value:Union[str, any] = None) -> None:
        self.builder = builder
        self.type = value_type
        self.value = raw_value
        # TODO: process raw_value into python value then set self.value = to the processed value


    def get_value(self):
        if isinstance(self.type, DataStructureType):
            if self.type.type == ScalarType.c8:
                return ir.Constant(self.type.value, bytearray(self.value.encode()))
        return self.type.value(self.value)
    
    def write(self) -> ir.AllocaInstr:
        if isinstance(self.value, ir.Instruction):
            return self.value
        else:
            const = self.get_value()
            ret_val = self.builder.cursor.alloca(const.type)
            self.builder.cursor.store(const, ret_val)
            return ret_val
    
    def to_ptr(self) -> ir.AllocaInstr:
        ptr = self.type.value.as_pointer()(self.value)#self.builder.cursor.inttoptr(self.get_value(), self.type.value)
        print(f"itp:{ptr}")
        return ptr
    
    def dbg_print(self):
        print(self.type.value)

    @property
    def is_pointer(self):
        return self.type.value.is_pointer
