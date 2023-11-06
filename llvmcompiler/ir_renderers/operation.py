from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from typing import List, Tuple, Union
from llvmlite import ir

from llvmcompiler.compiler_types.type import ScalarType, AnyType, ir_is_ptr, is_ptr, create_type
if TYPE_CHECKING:
    from .builder_data import BuilderData
import llvmcompiler.ir_renderers.variable as vari

class OperationType(Enum):
    define = 0
    assign = 1
    add = 2
    subtract = 3
    multiply = 4
    divide = 5
    collect = 6
    increment = 7
    decrement = 8
    call = 9
    function_return = 10
    define_heap = 11
    free_heap = 12
    cast = 13
    dereference = 14

class Operation:
    def __init__(self, operation:OperationType, arguments:List[Union[Operation, vari.Variable, AnyType, vari.Value, any, Tuple[str, vari.Variable]]] = []) -> None:
        self.builder:BuilderData = None
        self.operation = operation
        self.raw_arguments = arguments
        self.arguments = arguments

    def write(self):
        # process the arguments and run any operation arguments
        for r_a_n, raw_arg in enumerate(self.raw_arguments):
            if isinstance(raw_arg, Operation):
                inner_op = self.builder.scope.write_operation(raw_arg)
                self.arguments[r_a_n] = vari.Value(self.builder, create_type(inner_op.type), inner_op)
            else:
                self.arguments[r_a_n] = raw_arg

        # renders the operation to IR
        if self.operation == OperationType.define:
            # self.arguments: 0 = name, 1 = type, 2 = value
            self.builder.declare_variable(vari.Variable(self.builder, *self.arguments))

        elif self.operation == OperationType.define_heap:
            self.builder.declare_variable(vari.Variable(self.builder, *self.arguments, heap=True))

        elif self.operation == OperationType.free_heap:
            voidptr_ty = ir.IntType(8).as_pointer()
            ptr = self.builder.cursor.gep(self.arguments[0].variable, [ir.IntType(8)(0)], inbounds=True)
            # dbg_llvm_print(self.builder, ptr)
            bc = self.builder.cursor.bitcast(ptr, voidptr_ty)
            self.builder.cursor.call(self.builder.functions["deallocate"], [bc])

        elif self.operation == OperationType.assign:
            # self.arguments: 0 = variable, 1 = value
            self.builder.set_variable(self.arguments[0], self.arguments[1])

        elif self.operation == OperationType.function_return:
            self.builder.pop_variables()
            if len(self.arguments) == 0:
                # if type of function is not void then throw an error
                self.builder.cursor.ret_void()
            else:
                # if type of function does not match argument[0].type then throw error
                # self.arguments: 0 = type
                if ir_is_ptr(self.builder.function.return_value.type):
                    if self.arguments[0].is_pointer:
                        self.builder.cursor.ret(self.arguments[0])
                    else:
                        # throw error because function was expected to return a pointer
                        print(f"Error: Function expected to return a pointer, not {self.arguments[0].type}.")
                else:
                    # function does not return a pointer
                    if self.arguments[0].is_pointer:
                        self.builder.cursor.ret(self.arguments[0].load())
                    else:
                         self.builder.cursor.ret(self.arguments[0].load())

        elif self.operation == OperationType.call:
            # cast the arguments
            # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
            cast_arguments:List[Union[ir.AllocaInstr, ir.Constant, ir.CallInstr.CallInstr, any]] = []
            for a_n, argument in enumerate(self.arguments[1:]):
                arg = None

                if isinstance(argument, vari.Variable):
                    arg = argument.variable
                elif isinstance(argument, vari.Value):
                    arg = argument.write()
                
                

                if a_n < len(self.builder.functions[self.arguments[0][0]].args):
                    #cast to the right type
                    arg = self.builder.cursor.bitcast(arg, self.builder.functions[self.arguments[0][0]].args[a_n].type)

                    # we auto cast pointers for non variable_arg arguments
                    if arg.type.is_pointer:
                        if not self.builder.functions[self.arguments[0][0]].args[a_n].type.is_pointer:
                            while (arg.type.is_pointer):
                                arg = self.builder.cursor.load(arg)
                        cast_arguments.append(arg)
                    else:
                        # non pointers must be loaded before using
                        arg = self.builder.cursor.load(arg)
                        cast_arguments.append(arg)
                else:
                    cast_arguments.append(arg)
                    
            if len(self.arguments[0]) > 1:
                self.arguments[0][1].set(self.builder.cursor.call(self.builder.functions[self.arguments[0][0]], cast_arguments))
            else:
                return self.builder.cursor.call(self.builder.functions[self.arguments[0][0]], cast_arguments)
            
        elif self.operation == OperationType.cast:
            arg1, arg2 = None, None

            #process arg1
            if isinstance(self.arguments[0], vari.Variable):
                arg1 = self.arguments[0].variable
            elif isinstance(self.arguments[0], vari.Value):
                arg1 = self.arguments[0].write()
            
            arg2 = self.arguments[1].type.value

            return self.builder.cursor.bitcast(arg1, arg2)
        
        elif self.operation == OperationType.add:
            arg1, arg2 = None, None

            #process arg1
            if isinstance(self.arguments[0], vari.Variable):
                arg1 = self.arguments[0].load()
            elif isinstance(self.arguments[0], vari.Value):
                arg1 = self.arguments[0].get_value()
            
            #process arg1
            if isinstance(self.arguments[1], vari.Variable):
                arg2 = self.arguments[1].load()
            elif isinstance(self.arguments[1], vari.Value):
                arg2 = self.arguments[1].get_value()

            res = self.builder.cursor.add(arg1, arg2)
            return res
        
        elif self.operation == OperationType.subtract:
            arg1, arg2 = None, None

            #process arg1
            if isinstance(self.arguments[0], vari.Variable):
                arg1 = self.arguments[0].load()
            elif isinstance(self.arguments[0], vari.Value):
                arg1 = self.arguments[0].get_value()
            
            #process arg1
            if isinstance(self.arguments[1], vari.Variable):
                arg2 = self.arguments[1].load()
            elif isinstance(self.arguments[1], vari.Value):
                arg2 = self.arguments[1].get_value()

            return self.builder.cursor.sub(arg1, arg2)
        
        elif self.operation == OperationType.multiply:
            arg1, arg2 = None, None

            #process arg1
            if isinstance(self.arguments[0], vari.Variable):
                arg1 = self.arguments[0].load()
            elif isinstance(self.arguments[0], vari.Value):
                arg1 = self.arguments[0].get_value()
            
            #process arg1
            if isinstance(self.arguments[1], vari.Variable):
                arg2 = self.arguments[1].load()
            elif isinstance(self.arguments[1], vari.Value):
                arg2 = self.arguments[1].get_value()

            return self.builder.cursor.mul(arg1, arg2)
        
        elif self.operation == OperationType.divide:
            arg1, arg2 = None, None

            #process arg1
            if isinstance(self.arguments[0], vari.Variable):
                arg1 = self.arguments[0].load()
            elif isinstance(self.arguments[0], vari.Value):
                arg1 = self.arguments[0].get_value()
            
            #process arg1
            if isinstance(self.arguments[1], vari.Variable):
                arg2 = self.arguments[1].load()
            elif isinstance(self.arguments[1], vari.Value):
                arg2 = self.arguments[1].get_value()

            return self.builder.cursor.sdiv(arg1, arg2)
        
        elif self.operation == OperationType.dereference:

            #process arg1
            if not isinstance(self.arguments[0], vari.Variable):
                # throw error because the supplied token/item is not dereferenceable
                print(f"Error: {self.arguments[0]} cannot be dereferenced.")
            

            return self.arguments[0].load()

        

def dbg_llvm_print(builder:BuilderData, var):
    srcstr = "%i\n\00"
    string = builder.cursor.alloca(ir.ArrayType(ir.IntType(8), len(srcstr)))
    builder.cursor.store(ir.Constant(ir.ArrayType(ir.IntType(8), len(srcstr)), bytearray(srcstr.encode("utf8"))), string)
    builder.cursor.call(builder.functions["print"], [builder.cursor.bitcast(string, ScalarType.c8.value.as_pointer()), var])