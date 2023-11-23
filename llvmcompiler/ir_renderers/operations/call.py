from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition

class CallOperation(Operation):
    def __init__(self, function:str | Operation | Any, arguments: list[arg_type] = [], template_arguments:list[CompilerType] = []) -> None:
        super().__init__(arguments)
        self.template_arguments = template_arguments
        self.function:str | FunctionDefinition | Operation = function
    
    def get_function(self):
        if isinstance(self.function, Operation):
            self.function: tuple[ir.Instruction, FunctionDefinition] = self.write_argument(self.function)
        # link all templates to their functions.
        for t_a in range(len(self.template_arguments)):
            self.template_arguments[t_a].parent = self.builder.function
            self.template_arguments[t_a].module = self.builder.module
        
        f_to_c = None
        if isinstance(self.function, str):
            function_obj = self.builder.module.functions[self.function].get_function(self.template_arguments)
        elif isinstance(self.function, vari.Value):
            """
            This means that it is a member function.  The value of the Value should be a tuple containing (ir.Instruction, FunctionDefinition)
            """
            self.arguments.insert(0, self.function.get_value()[0])
            function_obj = self.function.get_value()[1].get_function(self.template_arguments)
            
        else:
            function_obj = self.function.get_function(self.template_arguments)


        f_to_c = function_obj.function
        return f_to_c
    

    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        
        f_to_c = self.get_function()



        if len(self.arguments) > 0:
            for a_n, argument in enumerate(self.get_variables(self.arguments, True)):
                
                arg = argument

                if isinstance(argument, vari.Variable):
                    arg = argument.variable
                elif isinstance(argument, vari.Value):
                    arg = argument.get_value()
                
                

                arg = self.process_arg(argument)
                arguments.append(arg)
        
        print(f_to_c.name)
        print(arguments)
        
        func_call = self.builder.cursor.call(f_to_c, arguments)


        self.builder.cursor.comment("OP::call end")

        return vari.Value(CompilerType.create_from(func_call.type), func_call.get_reference(), True)
    
    def __repr__(self) -> str:
        return f"({self.__class__.__name__} : {{function: {self.function}, arguments: {self.arguments}}})"