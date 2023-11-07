from __future__ import annotations
from typing import Dict, List, Union, TYPE_CHECKING
from llvmcompiler.compiler_types.type import ScalarType, DataStructureType, DataStructureTypeOptions, AnyType
from llvmlite import ir
from llvmcompiler.ir_renderers.builder_data import BuilderData
from llvmcompiler.ir_renderers.operation import Operation

import llvmcompiler.ir_renderers.variable as var

if TYPE_CHECKING:
    from llvmcompiler.modules.module import Module



class Function:
    def __init__(self, module:Module, name:str, arguments:Dict[str, AnyType], return_type:AnyType, variable_arguments:bool = False) -> None:
        self.module = module
        self.name = name
        self.arguments = arguments
        self.return_type = return_type
        self.variable_arguments = variable_arguments
        self.function_type = ir.FunctionType(self.return_type.value, [stype.value for stype in self.arguments.values()], var_arg=self.variable_arguments)
        self.function = ir.Function(self.module.module, self.function_type, self.name)
        
        # this is all variables within the function scope
        self.variables:Dict[str, var.Variable] = [{}]

        # name the function arguments
        for arg_num, arg in enumerate(self.arguments.keys()):
            self.function.args[arg_num].name = arg
        
        # get a ir cursor for writing ir to different things in the function
        self.entry = self.function.append_basic_block("entry")
        self.builder = BuilderData(self, ir.IRBuilder(self.entry), self.variables)
        # This cursor needs to be passed to any ir building classes that are used
        # within this function.

        self.get_variable = lambda var_name: self.builder._get_variable(var_name)
    
    def write_operation(self, operation:Operation):
        operation.builder = self.builder
        return operation.write()


    # functions used for debugging are prefixed with dbg
    def dbg_print(self):
        print(self.function)

    def dbg_print_module(self):
        print(self.module)