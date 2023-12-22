from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from .cast import CastOperation
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition
import llvmcompiler.ir_renderers.operations as ops

class CallOperation(Operation):
    def __init__(self, function:str | Operation | Any, arguments: list[arg_type] = None, template_arguments:list[CompilerType] = None, is_operator = False) -> None:
        super().__init__(arguments)
        self.template_arguments = [] if template_arguments == None else template_arguments
        self.function:str | FunctionDefinition | Operation = function
        self.is_member_function = False
        self.struct_operator = False
        self.is_operator = is_operator
    def write(self):
        if self.is_operator:
            for i in range(len(self.arguments)):
                self.arguments[i] = ops.AddressOperation([self.arguments[i]])
        return super().write()
    
    @lru_cache(32, True)
    def get_function(self):
        if isinstance(self.function, Operation):
            #print(self.function)
            self.function: tuple[ir.Instruction, FunctionDefinition] = self.write_argument(self.function)
            #print(self.function)
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
            self.is_member_function = True
        else:
            function_obj = self.function.get_function(self.template_arguments)


        f_to_c = function_obj.function
        return f_to_c
    
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        
        f_to_c = self.get_function()


        if len(self.arguments) > 0:
            for a_n, argument in enumerate(self.get_variables(self.arguments, True)):
                
                arg = argument

                
                if isinstance(arg, vari.Value):
                    if arg.is_literal and a_n < len(f_to_c.args):
                        #print(argument)
                        arg.type = CompilerType.create_from(
                            f_to_c.args[a_n].type,
                            self.builder.module,
                            self.builder.function
                            )



                arg = self.process_arg(arg)
                arguments.append(arg)
        
        #print("\n\n\nFUNC")

        #print(f_to_c.name)
        
        #print(arguments)
        
        func_call = self.builder.cursor.call(f_to_c, arguments)
        #print(func_call)

        self.builder.cursor.comment("OP::call end")


        return vari.Value(CompilerType.create_from(func_call.type, self.builder.module, self.builder.function), func_call, True, is_call=True, address=self.is_operator)
    
    def __repr__(self) -> str:
        return f"({self.__class__.__name__} : {{function: {self.function}, arguments: {self.arguments}}})"