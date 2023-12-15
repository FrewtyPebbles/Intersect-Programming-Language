from functools import lru_cache
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AssignOperation(Operation):
    def _write(self):
        # self.arguments: 0 = variable, 1 = value
        self.builder.cursor.comment("OP::assign START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        var = None
        
        if isinstance(self.arguments[0], vari.Value):
            # print([self.arguments[1], self.arguments[0].value])
            self.builder.cursor.store(self.process_arg(self.arguments[1]), self.arguments[0].value)
            
            var = self.arguments[0]
        elif isinstance(self.arguments[0], vari.Variable):
            #print(f"ASSIGN [{self.arguments[0]} = {self.arguments[1]}]")
            var = self.builder.set_variable(self.arguments[0], self.arguments[1])

        self.builder.cursor.comment("OP::assign END")
        # returns the variable that was assigned to so you can assign variables in operations
        return var