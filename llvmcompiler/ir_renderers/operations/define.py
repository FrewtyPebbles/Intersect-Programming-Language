from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DefineOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::define(stack) START")
        
        self.arguments[1].parent = self.builder.function
        self.arguments[1].module = self.builder.module
        var = self.builder.declare_variable(vari.Variable(self.builder, *self.arguments))
        self.builder.cursor.comment("OP::define(stack) END")
        return var