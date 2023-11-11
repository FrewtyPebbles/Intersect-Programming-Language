from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.function as fn

class CallOperation(Operation):
    def get_function(self):
        f_to_c = None
        if isinstance(self.arguments[0], tuple):
            # First argument is a tuple containing the function name and a list of template types
            
            f_name, template_arguments = self.arguments[0]
            # create the template function
            mangled_name = self.builder.module.functions[f_name].write(template_arguments)
            f_to_c = self.builder.module.functions[f_name].function[mangled_name]
        else:
            func = self.builder.functions[self.arguments[0]]
            if isinstance(func, fn.Function):
                f_to_c = func.function[func.name]
            if isinstance(func, ir.Function):
                f_to_c = func

        
        return f_to_c
    

    def _write(self):
        self.builder.cursor.comment("OP::call START")
        # cast the arguments
        # self.arguments: 0 = (name, ?return_variable), 1+ = n number of args
        cast_arguments:list[ir.AllocaInstr | ir.Constant | ir.CallInstr.CallInstr | any] = []
        
        f_to_c = self.get_function()



        if len(self.arguments) > 1:
            for a_n, argument in enumerate(self.get_variables(self.arguments[1], True)):
                
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
                
        print(cast_arguments)

        func_call = self.builder.cursor.call(f_to_c, cast_arguments)


        self.builder.cursor.comment("OP::call end")

        return vari.Value(CompilerType.create_from(func_call.type), func_call.get_reference(), True)