from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from copy import deepcopy

class AssignOperation(Operation):
    def _write(self):
        # self.arguments: 0 = variable, 1 = value
        self.builder.cursor.comment("OP::assign START")
        self.arguments = self.get_variables()
        if isinstance(self.arguments[1], vari.Value):
            if isinstance(self.arguments[1].value, int) or\
            self.arguments[1].value in {"true", "false"}:
                new_type = deepcopy(self.arguments[0].type)
                new_type.value = ir.IntType(new_type.size)
                self.arguments[1].type = new_type
        var = None
        if isinstance(self.arguments[0], vari.Variable):
            var = self.builder.set_variable(self.arguments[0], self.arguments[1])
        elif isinstance(self.arguments[0], vari.Value):
            self.builder.cursor.store(self.process_arg(self.arguments[1]), self.arguments[0].value)
            var = self.arguments[0]

        self.builder.cursor.comment("OP::assign END")
        # returns the variable that was assigned to so you can assign variables in operations
        return var