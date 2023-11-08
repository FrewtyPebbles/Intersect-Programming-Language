from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class MultiplyOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::multiply START")
            
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.mul(arg1, arg2)
        self.builder.cursor.comment("OP::multiply END")

        return vari.Value(self.arguments[0].type, res.get_reference(), True)