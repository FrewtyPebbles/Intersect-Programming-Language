from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.compiler_types as ct

class DefineOperation(Operation):
    def __init__(self, arguments: list[arg_type] = None, force_type:ct.CompilerType = None) -> None:
        super().__init__(arguments)
        self.force_type = force_type
    def _write(self):
        self.builder.cursor.comment("OP::define(stack) START")
        
        self.arguments[1].parent = self.builder.function
        self.arguments[1].module = self.builder.module
        if self.force_type != None:
            self.arguments[1].type = self.force_type
        
        var = self.builder.declare_variable(vari.Variable(self.builder, *self.arguments))
        self.builder.cursor.comment("OP::define(stack) END")
        return var