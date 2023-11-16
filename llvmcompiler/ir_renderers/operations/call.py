from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition

class CallOperation(Operation):
    def __init__(self, function:str, arguments: list[arg_type] = [], template_arguments:list[CompilerType] = []) -> None:
        super().__init__(arguments)
        self.template_arguments = template_arguments
        self.function:str | FunctionDefinition = function
    
    def get_function(self):
        # link all templates to their functions.
        for t_a in range(len(self.template_arguments)):
            self.template_arguments[t_a].parent = self.builder.function
            self.template_arguments[t_a].module = self.builder.module
        
        f_to_c = None
        if isinstance(self.function, str):
            function_obj = self.builder.module.functions[self.function].get_function(self.template_arguments)
        else:
            function_obj = self.function.get_function(self.template_arguments)


        f_to_c = function_obj.function
        return f_to_c
    

    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        cast_arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        
        f_to_c = self.get_function()



        if len(self.arguments) > 0:
            for a_n, argument in enumerate(self.get_variables(self.arguments, True)):
                
                arg = None

                if isinstance(argument, vari.Variable):
                    arg = argument.variable
                elif isinstance(argument, vari.Value):
                    arg = argument.write()
                
                

                if a_n < len(f_to_c.args):
                    #cast to the right type
                    arg = self.builder.cursor.bitcast(arg, f_to_c.args[a_n].type)
                    
                    # we auto cast pointers for non variable_arg arguments
                    cast_arguments.append(arg)
                else:
                    arg = self.process_arg(argument)
                    cast_arguments.append(arg)
        

        func_call = self.builder.cursor.call(f_to_c, cast_arguments)


        self.builder.cursor.comment("OP::call end")

        return vari.Value(CompilerType.create_from(func_call.type), func_call.get_reference(), True)