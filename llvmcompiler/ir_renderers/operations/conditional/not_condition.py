import llvmcompiler.compiler_types as ct
from ...operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class NotOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::and START")
        self.arguments = self.get_variables()
        
        #process args
        arg = self.process_arg(self.arguments[0])

        res:ir.Instruction = self.builder.cursor.icmp_unsigned("==", ir.IntType(1)(0), arg)
        self.builder.cursor.comment("OP::and END")

        return vari.Value(ct.BoolType(), res, True)