from __future__ import annotations

from typing import Dict, List, Union
from llvmlite import ir
from typing import TYPE_CHECKING
from .variable import Variable, Value

class BuilderData:
    def __init__(self, module:ir.Module, function:ir.Function, builder:ir.IRBuilder, variables:List[Dict[str, Variable]]) -> None:
        self.module = module
        self.cursor = builder
        self.variables_stack = variables
        self.function = function

        # this is where all function names/labels are defined
        self.functions = {
            # The key is the name that is parsed from source code,
            # the value is the llvm function.
            "print": self._std_printf(),
            #"input":"input" # will be getting input function from c dll/so file via this method https://stackoverflow.com/questions/36658726/link-c-in-llvmlite
        }

    def declare_variable(self, variable:Variable):
        self.variables_stack[len(self.variables_stack)-1][variable.name] = variable

    def set_variable(self, variable_name:str, value:Union[Variable, Value, any]):
        if isinstance(value, Value):
            self.variables_stack[len(self.variables_stack)-1][variable_name].value = value
            var = self._get_variable(variable_name)
            self.cursor.store(value.type.value(value.value), var.variable)
        elif isinstance(value, Variable):
            self.variables_stack[len(self.variables_stack)-1][variable_name].value = value
            var = self._get_variable(variable_name)
            self.cursor.store(value.load(), var.variable)
        else:
            # This is for inline operations,  ir ordering is handled by LLVM
            self.variables_stack[len(self.variables_stack)-1][variable_name].value = value
            var = self._get_variable(variable_name)
            self.cursor.store(value, var.variable)

    def _get_variable(self, name:str) -> Variable:
        for layer_number, layer in enumerate(self.variables_stack):
            if name in layer.keys():
                return self.variables_stack[layer_number][name]
            
    def call_function(self, name:str, arguments:List[Union[Variable, Value]]) -> ir.CallInstr.CallInstr:
        # cast the arguments
        cast_arguments:List[Union[ir.AllocaInstr, ir.Constant]] = []
        for a_n, argument in enumerate(arguments):
            arg = None

            if isinstance(argument, Variable):
                arg = argument.variable
            elif isinstance(argument, Value):
                arg = argument.write()
            
            if a_n < len(self.functions[name].args):
                #cast to the right type
                arg = self.cursor.bitcast(arg, self.functions[name].args[a_n].type)
            
            cast_arguments.append(arg)
                
        
        return self.cursor.call(self.functions[name], cast_arguments)

    # Standard library function declarations.
    def _std_printf(self) -> ir.Function:
        # this creates the IR for printf
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        return printf