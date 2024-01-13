from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from typing import TYPE_CHECKING, Self
from enum import Enum
from typing import List, Tuple, Union
from llvmlite import ir


import llvmcompiler.compiler_types as ct
if TYPE_CHECKING:
    from .builder_data import BuilderData
from llvmcompiler.ir_renderers.variable import Variable, Value, HeapValue
import llvmcompiler.ir_renderers.operations as ops
import llvmcompiler.ir_renderers.struct as st


arg_type = Self | Variable | ct.CompilerType | Value | Tuple[str, Variable]

class Operation:
    """
    All operations inherit from this operation
    """
    def __init__(self, arguments:list[arg_type] = None, token = None) -> None:
        self.builder:BuilderData = None
        self.raw_arguments = [] if arguments == None else arguments
        self.arguments = [] if arguments == None else arguments
        self.op_token = "+"
        self.struct_operator = True
        self.token = token

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"builder"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result
    

    def get_variables(self, arguments: list[arg_type] = None, no_default_action = False):
        arguments = [] if arguments == None else arguments
        if len(arguments) == 0 and not no_default_action:
            arguments = self.arguments
        new_args = [*arguments]
        for a_n, a in enumerate(arguments):
            if isinstance(a, str):
                new_args[a_n] = self.get_variable(a)
            else:
                new_args[a_n].builder = self.builder
        
        return new_args

    @lru_cache(32, True)
    def get_variable(self, var_name:str):
        return self.builder.get_variable(var_name)

    def set_arguments_parent(self):
        for a_n in range(len(self.arguments)):
            self.arguments[a_n].parent = self.builder.function
            self.arguments[a_n].module = self.builder.module

    @lru_cache(32, True)
    def process_arg(self, arg:arg_type, dont_load = False):
        if isinstance(arg, str):
            arg = self.builder.get_variable(arg)
            arg.parent = self.builder.function
            arg.module = self.builder.module
            return arg
        if isinstance(arg, Variable):
            arg.parent = self.builder.function
            arg.module = self.builder.module
            if arg.function_argument or dont_load:
                return arg.variable
            else:
                return arg.load()
        elif isinstance(arg, Value):
            arg.parent = self.builder.function
            arg.module = self.builder.module
            return arg.get_value()
        else:
            return arg
        
    @lru_cache(32, True)
    def process_lhs_rhs_args(self, dont_load = False):
        #process arg1
        arg1 = self.process_arg(self.arguments[0], dont_load)
        
        #process arg2
        arg2 = self.process_arg(self.arguments[1], dont_load)

        return arg1, arg2
    
    def convert_literal_types(self):
        compare_arg = self.arguments[0]
        for a_n in range(len(self.arguments)):
            compare_arg = self.arguments[a_n]
            if compare_arg.is_instruction:
                break
        for a_n in range(len(self.arguments)):
            if not self.arguments[a_n].is_instruction:
                if isinstance(self.arguments[a_n].value, int) or\
                self.arguments[a_n].value in {"true", "false"}:
                    new_type = compare_arg.type
                    new_type.value = ir.IntType(new_type.size)
                    self.arguments[1].type = new_type
            

    @lru_cache(32, True)
    def write_argument(self, raw_arg: arg_type):
        if isinstance(raw_arg, Operation):
            value = self.builder.function.create_operation(raw_arg).write()
            value.parent = self.builder.function
            value.module = self.builder.function.module
            value.builder = self.builder
            return value
        elif isinstance(raw_arg, Value):
            raw_arg.parent = self.builder.function
            raw_arg.module = self.builder.module
            raw_arg.builder = self.builder
            if isinstance(raw_arg, HeapValue):
                raw_arg.render_heap()
            return raw_arg
        else:
            return raw_arg

    def write_arguments(self):
        """
        This function processes the arguments of the operation and runs any operation arguments.
        """

        # process the arguments and run any operation arguments
        for r_a_n, raw_arg in enumerate(self.raw_arguments):
            self.arguments[r_a_n] = self.write_argument(raw_arg)

        

    def _write(self) -> Value | Variable:
        """
        This should be overridden to in inheriting class.
        This function is what is called to write the ir for the operation
        """
        

    def write(self):
        self.write_arguments()
        #print(self.__class__.__name__)
        if self.struct_operator:
            op_arguments = self.get_variables()
            #print("\tIS VALID CLASS OP")
            for i in range(len(op_arguments)):
                while isinstance(op_arguments[i].type, ct.Template):
                    op_arguments[1].type = op_arguments[1].type.get_template_type()
            
            #print(self.op_token, "  ", op_arguments[1].type)
            if isinstance(op_arguments[0].type, st.StructType):
                
                if op_arguments[0].type.ptr_count <= 1:
                    # try:
                    #     print(op_arguments[1].type)
                    # except: pass
                    if len(op_arguments) > 1:
                        op_func = self.call_operator_function(op_arguments[0], op_arguments[1])
                        if op_func != None:
                            return op_func
                    else:
                        op_func = self.call_operator_function(op_arguments[0])
                        if op_func != None:
                            return op_func
        
        return self._write()
    
    def call_operator_function(self, this: arg_type, other: arg_type = None):
        if other == None:
            
            func = this.type.struct.get_operator(self.op_token, True)
            if func == None: return None
            #print(func)
            call = ops.CallOperation(func, [this], is_operator=True)
            call.builder = self.builder
            return call.write()
        #print(this.type)
        #print(self.op_token)
        func = this.type.struct.get_operator(self.op_token, True, arg_type=other.type)
        if func == None: return None
        #print(func)
        call = ops.CallOperation(func, [this, other], is_operator=True)
        call.builder = self.builder
        return call.write()
    
    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f"({self.__class__.__name__} : {{arguments: {self.arguments}}})"

        

        

def dbg_llvm_print(builder:BuilderData, var):
    srcstr = "%i\n\00"
    string = builder.alloca(ir.ArrayType(ir.IntType(8), len(srcstr)))
    builder.cursor.store(ir.Constant(ir.ArrayType(ir.IntType(8), len(srcstr)), bytearray(srcstr.encode("utf8"))), string)
    builder.cursor.call(builder.functions["print"].get_function().function, [builder.cursor.bitcast(string, ct.C8Type().cast_ptr()), var])