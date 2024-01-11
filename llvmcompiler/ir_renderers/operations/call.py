from functools import lru_cache
import llvmcompiler.compiler_types as ct
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from .cast import CastOperation
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition
import llvmcompiler.ir_renderers.operations as ops

class CallOperation(Operation):
    def __init__(self, function:str | Operation | Any, arguments: list[arg_type] = None, template_arguments:list[ct.CompilerType] = None, is_operator = False) -> None:
        super().__init__(arguments)
        self.template_arguments = [] if template_arguments == None else template_arguments
        self.function:str | FunctionDefinition | Operation = function
        self.is_member_function = False
        self.struct_operator = False
        self.is_operator = is_operator
        self.ret_type = None
        self.virtual = False

    def write(self):
        if self.is_operator:
            for i in range(len(self.arguments)):
                self.arguments[i] = ops.AddressOperation([self.arguments[i]])
        return super().write()
    
    @lru_cache(32, True)
    def get_function(self):
        
        #print("F0: ", self.function)
        if isinstance(self.function, Operation):
            #print("F1: ", self.function)
            self.function: tuple[ir.Instruction, FunctionDefinition] = self.write_argument(self.function)
        # link all templates to their functions.
        for t_a in range(len(self.template_arguments)):
            self.template_arguments[t_a].parent = self.builder.function
            self.template_arguments[t_a].module = self.builder.module
        
        
        f_to_c = None
        if isinstance(self.function, str):
            function_obj = self.builder.module.functions[self.function].get_function(self.template_arguments)
            self.ret_type = function_obj.return_type
        elif isinstance(self.function, vari.Value):
            """
            This means that it is a member function.  The value of the Value should be a tuple containing (ir.Instruction, FunctionDefinition) if it is a static function.

            If it is a virtual function, it should be a value containing a gep instruction for the function.
            """
            function_value = self.function.get_value()
            
            
            
            if isinstance(gep_instr := function_value[1], ir.GEPInstr):
                #Virtual function
                self.arguments.insert(0, function_value[0])
                function_obj = self.builder.cursor.load(gep_instr)
                base = gep_instr.type.pointee
                while isinstance(base, ir.PointerType):
                    base = base.pointee
                self.ret_type = base.return_type
                self.virtual = True
                
                self.is_member_function = True
            else:
                #Static function
                self.arguments.insert(0, self.function.get_value()[0])
                function_obj = self.function.get_value()[1].get_function(self.template_arguments)
                self.ret_type = function_obj.return_type
                self.is_member_function = True

                

        else:
            function_obj = self.function.get_function(self.template_arguments)
            self.ret_type = function_obj.return_type


        while isinstance(self.ret_type, ct.Template):
            self.ret_type = self.ret_type.get_template_type()
        
        f_to_c = function_obj if self.virtual else function_obj.function
        
        return f_to_c
    
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        #print("FUNC")
        
        f_to_c = self.get_function()
        

        if len(self.arguments) > 0:
            for a_n, argument in enumerate(self.get_variables(self.arguments, True)):
                
                arg = argument

                
                if not self.virtual and isinstance(arg, vari.Value):
                    if arg.is_literal and a_n < len(f_to_c.args):
                        #print(argument)
                        arg.type = ct.CompilerType.create_from(
                            f_to_c.args[a_n].type,
                            self.builder.module,
                            self.builder.function
                            )



                arg = self.process_arg(arg)
                arguments.append(arg)
        #print(self.function, self.arguments)
        #print("\n\n\nFUNC")

        #print(f_to_c.name)
        
        #print(arguments)
        #self.builder.module.dbg_print()
        #print("FUNC Name")
        #print(f_to_c.name)
        func_call = self.builder.cursor.call(f_to_c, arguments)
        #print(func_call)

        self.builder.cursor.comment("OP::call end")

        #print(self.function)
        
        return vari.Value(self.ret_type, func_call, True, is_call=True, address=self.is_operator)
    
    def __repr__(self) -> str:
        return f"({self.__class__.__name__} : {{function: {self.function}, arguments: {self.arguments}}})"