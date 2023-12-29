from functools import lru_cache

from llvmcompiler.ir_renderers.operation import arg_type
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AssignOperation(Operation):
    def __init__(self, arguments: list[arg_type] = None) -> None:
        super().__init__(arguments)
        self.op_token = "="
        #self.struct_operator = False # BUG: FOR NOW KEEP THIS HERE BUT DELETE ONCE A SOLUTION IS FOUND FOR POINTER/MEMORY ASSIGNMENT
    def _write(self):
        # self.arguments: 0 = variable, 1 = value
        self.builder.cursor.comment("OP::assign START")
        self.arguments = self.get_variables()
        
        self.convert_literal_types()
        var = None
        
        if isinstance(self.arguments[0], vari.Value):
            #print(f"\nASSIGN VAL [{self.arguments[0]} = {self.arguments[1]}]")
            self.builder.cursor.store(self.process_arg(self.arguments[1]), self.arguments[0].value)
            
            var = self.arguments[0]
        elif isinstance(self.arguments[0], vari.Variable):
            #print(f"\nASSIGN [{self.arguments[0]} = {self.arguments[1]}]")
            var = self.builder.set_variable(self.arguments[0], self.arguments[1])

        self.builder.cursor.comment("OP::assign END")
        # returns the variable that was assigned to so you can assign variables in operations
        
        return var