from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DefineHeapOperation(Operation):
    def _write(self):
        self.builder.cursor.comment(" OP::define(heap) START")
        self.arguments[1].parent = self.builder.function
        self.arguments[1].module = self.builder.module
        var = self.builder.declare_variable(vari.Variable(self.builder, *self.arguments, heap=True))
        self.builder.cursor.comment(" OP::define(heap) END")
        return var