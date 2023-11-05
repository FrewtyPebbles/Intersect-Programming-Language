from enum import Enum
from typing import List, Tuple, Union
from llvmlite import ir

from llvmcompiler.compiler_types.type import ScalarType, AnyType, ir_is_ptr, is_ptr
from .builder_data import BuilderData
from .variable import Value, Variable

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

class Operation:
    def __init__(self, operation:OperationType, arguments:List[Union[Variable, AnyType, Value, Tuple[str, Variable]]] = []) -> None:
        self.builder:BuilderData = None
        self.operation = operation
        self.arguments = arguments

    def write(self):
        # renders the operation to IR
        if self.operation == OperationType.define:
            # self.arguments: 0 = name, 1 = type, 2 = value
            self.builder.declare_variable(Variable(self.builder, *self.arguments))

        elif self.operation == OperationType.assign:
            # self.arguments: 0 = name, 1 = value
            self.builder.set_variable(self.arguments[0], self.arguments[1])

        elif self.operation == OperationType.function_return:
            if len(self.arguments) == 0:
                # if type of function is not void then throw an error
                self.builder.cursor.ret_void()
            else:
                # if type of function does not match argument[0].type then throw error
                # self.arguments: 0 = type
                if ir_is_ptr(self.builder.function.return_value.type):
                    if self.arguments[0].is_ptr():
                        self.builder.cursor.ret(self.arguments[0])
                    else:
                        # throw error because function was expected to return a pointer
                        print(f"Error: Function expected to return a pointer, not {self.arguments[0].type}.")
                else:
                    # function does not return a pointer
                    if self.arguments[0].is_ptr():
                        self.builder.cursor.ret(self.arguments[0])
                    else:
                         self.builder.cursor.ret(self.arguments[0].load())

        elif self.operation == OperationType.call:
            # cast the arguments
            # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
            cast_arguments:List[Union[ir.AllocaInstr, ir.Constant]] = []
            for a_n, argument in enumerate(self.arguments[1:]):
                arg = None

                if isinstance(argument, Variable):
                    arg = argument.variable
                elif isinstance(argument, Value):
                    arg = argument.write()
                
                if a_n < len(self.builder.functions[self.arguments[0][0]].args):
                    #cast to the right type
                    arg = self.builder.cursor.bitcast(arg, self.builder.functions[self.arguments[0][0]].args[a_n].type)

                if is_ptr(argument.type):
                    cast_arguments.append(arg)
                else:
                    # non pointers must be loaded before using
                    arg = self.builder.cursor.load(arg)
                    cast_arguments.append(arg)
                    
            if len(self.arguments[0]) > 1:
                self.arguments[0][1].set(self.builder.cursor.call(self.builder.functions[self.arguments[0][0]], cast_arguments))
            else:
                self.builder.cursor.call(self.builder.functions[self.arguments[0][0]], cast_arguments)

