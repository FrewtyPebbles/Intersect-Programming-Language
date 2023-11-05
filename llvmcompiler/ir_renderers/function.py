from typing import Dict, List, Union
from llvmcompiler.compiler_types.type import ScalarType, DataStructureType, DataStructureTypeOptions, AnyType
from llvmlite import ir
from llvmcompiler.ir_renderers.builder_data import BuilderData
from llvmcompiler.ir_renderers.operation import Operation

import llvmcompiler.ir_renderers.variable as var



class Function:
    def __init__(self, module:ir.Module, name:str, arguments:Dict[str, AnyType], return_type:AnyType, variable_arguments:bool = False) -> None:
        self.module = module
        self.name = name
        self.arguments = arguments
        self.return_type = return_type
        self.variable_arguments = variable_arguments
        self.function_type = ir.FunctionType(self.return_type.value, [stype.value for stype in self.arguments.values()], var_arg=self.variable_arguments)
        self.function = ir.Function(self.module, self.function_type, self.name)
        
        # this is all variables within the function scope
        self.variables:Dict[str, var.Variable] = [{}]

        # name the function arguments
        for arg_num, arg in enumerate(self.arguments.keys()):
            self.function.args[arg_num].name = arg
        
        # get a ir cursor for writing ir to different things in the function
        self.builder = BuilderData(self.module, self.function, ir.IRBuilder(self.function.append_basic_block("entry")), self.variables)
        # This cursor needs to be passed to any ir building classes that are used
        # within this function.

        self.get_variable = lambda var_name: self.builder._get_variable(var_name)
    
    def write_operation(self, operation:Operation):
        operation.builder = self.builder
        return operation.write()

    def write_call(self, name:str, arguments:List[Union[var.Variable, var.Value]]):
        return self.builder.call_function(name, arguments)

    # functions used for debugging are prefixed with dbg
    def dbg_print(self):
        print(self.function)