from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AssignOperation(Operation):
    def _write(self):
        # self.arguments: 0 = variable, 1 = value
        self.builder.cursor.comment("OP::assign START")
        print(self.arguments)
        var = self.builder.set_variable(self.arguments[0], self.arguments[1])
        self.builder.cursor.comment("OP::assign END")
        # returns the variable that was assigned to so you can assign variables in operations
        return var