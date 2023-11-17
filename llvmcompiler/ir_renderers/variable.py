from __future__ import annotations

from llvmlite import ir

import llvmcompiler.compiler_types as ct
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .builder_data import BuilderData
    import llvmcompiler.ir_renderers.function as fn

import sys


IS_64BIT = sys.maxsize > 2**32

SIZE_T = ir.IntType(1)
if IS_64BIT:
    SIZE_T = ir.IntType(64)
else:
    SIZE_T = ir.IntType(32)

class Variable:
    def __init__(self, builder:BuilderData, name:str, value:Value, heap = False, function_argument = False):
        self.builder = builder
        self.name = name
        self.value = value
        self.value.parent = self.builder.function
        self.value.module = self.builder.module
        self.heap = heap # wether a variable is stored on the heap or not
        self.function_argument = function_argument # wether or not the variable represents a function argument
        self.type = self.value.type.cast_ptr() if self.heap else self.value.type
        self.is_instruction = True
        self.module = self.builder.module

        # declare the variable
        if not self.function_argument:
            self.allocate()
        else:
            self.variable = self.value.value

        self.builder.declare_variable(self)

        if not self.function_argument:
            if self.value.value != None:
                self.set(self.value)
        
    def allocate(self):
        if self.heap:
            malloc_call = self.builder.cursor.call(self.builder.functions["allocate"].get_function().function, [SIZE_T(self.value.type.size)])
            self.type.parent = self.builder.function
            self.type.module = self.builder.module
            self.type.builder = self.builder
            bc = self.builder.cursor.bitcast(malloc_call, self.type.value)

            self.variable = self.builder.cursor.gep(bc, [ir.IntType(32)(0)], inbounds=True, name = self.name)
            
        else:
            self.variable = self.builder.alloca(self.type.value, name = self.name)        
    
    def set(self, value:Union[Variable, Value, any]):
        self.builder.set_variable(self, value)

    def load(self):
        return self.builder.cursor.load(self.variable)
    
    def __repr__(self) -> str:
        return f"(Variable:[name:\"{self.name}\"|value:{self.value}])"
    
    @property
    def is_pointer(self):
        return self.type.value.is_pointer
    
class Value:
    def __init__(self, value_type:ct.CompilerType, raw_value:Union[str, any] = None, is_instruction = False, heap = False, dbg_tag = "") -> None:
        self._builder:BuilderData = None
        self.type = value_type
        self.value = raw_value
        self.is_instruction = is_instruction
        self.heap = heap
        self._parent:fn.Function = None
        self.dbg_tag = dbg_tag
        self.module = None

    

    @property
    def parent(self):
        self.type.parent = self._parent
        self.type.module = self._parent.module
        return self._parent
    
    @parent.setter
    def parent(self, par:fn.Function):
        self._parent = par
        self.type.parent = par
        self.type.module = par.module

    @property
    def builder(self):
        return self._builder

    @builder.setter
    def builder(self, value:BuilderData):
        self._builder = value
        self.type.parent = self._builder.function
        self.type.module = self._builder.module
        

    def get_value(self):
        if self.is_instruction and not isinstance(self.value, str):
            return self.value
        if isinstance(self.type, ct.ArrayType):
            if isinstance(self.type.type.get_template_type(), ct.C8Type) if \
            isinstance(self.type.type, ct.Template) else \
            isinstance(self.type.type, ct.C8Type):
                return ir.Constant(self.type.value, bytearray(self.value.encode()))
            
        return self.type.value(self.value)
    
    def write(self) -> ir.AllocaInstr:
        if isinstance(self.value, ir.Instruction):
            return self.value
        else:
            const = self.get_value()
            ret_val = self.builder.alloca(const.type)
            self.builder.cursor.store(const, ret_val)
            return ret_val
    
    def to_ptr(self) -> ir.PointerType:
        ptr = self.type.value.as_pointer()(self.value)#self.builder.cursor.inttoptr(self.get_value(), self.type.value)
        return ptr
    
    def dbg_print(self):
        print(self.type.value)

    def __repr__(self) -> str:
        return f"(Value:[type:\"{self.type.value}\"|value:{self.value}]{{DBGTAG:\"{self.dbg_tag}\"}})"

    @property
    def is_pointer(self):
        return self.type.value.is_pointer
    
class HeapValue(Value):
    """
    This will add a value to the heap when it is read.
    """
    def render_heap(self):
        malloc_call = self.builder.cursor.call(self.builder.functions["allocate"].get_function().function, [SIZE_T(self.type.cast_ptr().size)])
        bc = self.builder.cursor.bitcast(malloc_call, self.type.cast_ptr().value)
        ptr = self.builder.cursor.gep(bc, [ir.IntType(32)(0)], inbounds=True)
        val = self.get_value()
        # if isinstance(self.type, ct.PrecisionType):
        #     if isinstance(self.type, ct.F32Type):
        #         fti = self.builder.cursor.fptosi(self.get_value(), ir.IntType(32))
        #         val = self.builder.cursor.inttoptr(fti, ir.IntType(32).as_pointer())
        #     elif isinstance(self.type, ct.D64Type):
        #         fti = self.builder.cursor.fptosi(self.get_value(), ir.IntType(64))
        #         val = self.builder.cursor.inttoptr(fti, ir.IntType(64).as_pointer())
        # elif isinstance(self.type, ct.IntegerType):
        #     val = self.builder.cursor.inttoptr(self.get_value(), self.type.value.as_pointer())
        print(f"{val} ||| {ptr}")
        self.builder.cursor.store(val, ptr)
        self.value = ptr
        self.is_instruction = True
        self.builder.push_value_heap(self.value)

    

class InstructionValue(Value):
    def __init__(self, value_type: ct.CompilerType, raw_value: str = None, is_instruction=False, heap=False) -> None:
        super().__init__(value_type, raw_value, is_instruction, heap)
        
    def get_value(self):
        self.value
