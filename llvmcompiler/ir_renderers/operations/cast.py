from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class CastOperation(Operation):
    def _write(self):
        arg1, arg2 = None, None
            
        self.builder.cursor.comment("OP::cast START")

        #process arg1
        if isinstance(self.arguments[0], vari.Variable):
            arg1 = self.arguments[0].variable
        elif isinstance(self.arguments[0], vari.Value):
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

        bitcast = self.builder.cursor.bitcast(arg1, arg2.value)

        self.builder.cursor.comment("OP::cast END")

        return vari.Value(self.builder, arg2, bitcast, True)