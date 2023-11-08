from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class CallOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        cast_arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        for a_n, argument in enumerate(self.arguments[1:]):
            arg = None

            if isinstance(argument, vari.Variable):
                arg = argument.variable
            elif isinstance(argument, vari.Value):
                arg = argument.get_value()
            
            

            if a_n < len(self.builder.functions[self.arguments[0]].args):
                #cast to the right type
                arg = self.builder.cursor.bitcast(arg, self.builder.functions[self.arguments[0]].args[a_n].type)
                
                # we auto cast pointers for non variable_arg arguments
                cast_arguments.append(arg)
            else:
                if isinstance(argument, vari.Variable):
                    if not argument.is_pointer:
                        arg = self.builder.cursor.load(arg)
                cast_arguments.append(arg)
                
        func_call = self.builder.cursor.call(self.builder.functions[self.arguments[0]], cast_arguments)

        self.builder.cursor.comment("OP::call end")

        return vari.Value(self.builder, CompilerType.create_from(func_call.type), func_call.get_reference(), True)