from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from copy import deepcopy

class AssignOperation(Operation):
    def _write(self):
        # self.arguments: 0 = variable, 1 = value
        self.builder.cursor.comment("OP::assign START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        var = None
        if isinstance(self.arguments[0], vari.Variable):
            var = self.builder.set_variable(self.arguments[0], self.arguments[1])
        elif isinstance(self.arguments[0], vari.Value):
            try:
                self.builder.cursor.store(self.process_arg(self.arguments[1]), self.arguments[0].value)
            # TODO: inttoptr might not be the best solution to this problem.
            # Search for a better solution
            except TypeError:
                int_to_ptr = self.builder.cursor.inttoptr(self.process_arg(self.arguments[1]), self.arguments[0].type.value.pointee)
                self.builder.cursor.store(int_to_ptr, self.arguments[0].value)
            var = self.arguments[0]

        self.builder.cursor.comment("OP::assign END")
        # returns the variable that was assigned to so you can assign variables in operations
        return var