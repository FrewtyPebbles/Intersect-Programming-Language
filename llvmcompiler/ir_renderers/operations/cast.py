from llvmcompiler.compiler_types import CompilerType, IntegerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.struct as st

class CastOperation(Operation):
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

        if not isinstance(self.arguments[0].type, IntegerType) or self.arguments[0].type.is_pointer:
            cast = self.builder.cursor.bitcast(arg1, arg2.value)
        elif self.arguments[0].type.size > self.arguments[1].size:
            # downcast
            cast = self.builder.cursor.trunc(arg1, arg2.value)
            #print("Downcast")
        elif self.arguments[0].type.size < self.arguments[1].size:
            # upcast
            cast = self.builder.cursor.sext(arg1, arg2.value)
            #print("Upcast")
        else:
            print("Error: Invalid cast")
            raise RuntimeError("invalid cast")
        

        self.builder.cursor.comment("OP::cast END")

        return vari.Value(arg2, cast, True)