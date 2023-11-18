from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class BreakOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::break START")
        self.arguments = self.get_variables()
        #need to figure out how to pop until exit scope is reached
        print("break")
        
        self.builder.cursor.branch(self.builder.break_scope())
        self.builder.cursor.comment("OP::break END")
