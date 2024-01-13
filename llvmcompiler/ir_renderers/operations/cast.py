from llvmcompiler.compiler_errors.comp_error import CompilerError
from llvmcompiler.compiler_types import ct
from llvmcompiler.ir_renderers.operation import arg_type
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.struct as st

class CastOperation(Operation):
    def __init__(self, arguments: list[arg_type] = None, token = None) -> None:
        super().__init__(arguments, token)
        self.struct_operator = False
    def _write(self):
        arg1, arg2 = None, None
            
        self.builder.cursor.comment("OP::cast START")
        self.arguments = self.get_variables()
        self.set_arguments_parent()

        #process arg1
        if isinstance(self.arguments[0], vari.Variable):
            arg1 = self.arguments[0].variable
        elif isinstance(self.arguments[0], vari.Value):
            # If casting a literal, just cast at compile time and return a constant of the type
            if self.arguments[0].is_instruction:
                arg1 = self.arguments[0].get_value()
            else:
                arg1 = self.arguments[0].write()
        
        if isinstance(self.arguments[1], vari.Variable):
            # if variable is passed
            arg2 = self.arguments[1].type
        elif isinstance(self.arguments[1], vari.Value):
            # if value is passed
            arg2 = self.arguments[1].type
        else:
            # if type is passed
            arg2 = self.arguments[1]
        cast = None
        a0_type = self.arguments[0].type
        if isinstance(a0_type, ct.Template):
            #print(self.arguments[0], " ", self.arguments[1])
            a0_type = a0_type.get_template_type()
            
        if (isinstance(a0_type, ct.I8Type) and isinstance(self.arguments[1], ct.C8Type) or isinstance(a0_type, ct.C8Type) and isinstance(self.arguments[1], ct.I8Type)) and  not a0_type.is_pointer:
            return vari.Value(arg2, arg1, True)
        elif  arg1.type.is_pointer or (not isinstance(a0_type, ct.IntegerType) and not isinstance(a0_type, ct.C8Type)):
            cast = self.builder.cursor.bitcast(arg1, arg2.value)
        elif a0_type.size > self.arguments[1].size:
            # downcast
            
            cast = self.builder.cursor.trunc(arg1, arg2.value)
            #print("Downcast")
        elif a0_type.size < self.arguments[1].size:
            # upcast
            cast = self.builder.cursor.sext(arg1, arg2.value)
            #print("Upcast")
        else:
            CompilerError( self.token,
                f"Invalid cast from {a0_type} to {arg2}.",
            ).throw()
        

        self.builder.cursor.comment("OP::cast END")

        return vari.Value(arg2, cast, True)