from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DivideOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::divide START")
            
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.sdiv(arg1, arg2)
        self.builder.cursor.comment("OP::divide END")

        return vari.Value(self.builder, self.arguments[0].type, res.get_reference(), True)