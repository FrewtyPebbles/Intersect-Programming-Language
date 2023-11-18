from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class BreakOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::return START")
        self.arguments = self.get_variables()
        #need to figure out how to pop until exit scope is reached
        print("break")
        self.builder.pop_variables()
        self.builder.cursor.branch(self.builder.break_scope())
        self.builder.module.dbg_print()
        self.builder.cursor.comment("OP::return END")
