from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DefineOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::define(stack) START")
        var = self.builder.declare_variable(vari.Variable(self.builder, *self.arguments))
        self.builder.cursor.comment("OP::define(stack) END")
        return var