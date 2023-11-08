from llvmcompiler.compiler_types.type import CompilerType
from ...operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class LessThanOrEqualToOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::less_than_or_equal_to START")
            
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.icmp_signed('<=', arg1, arg2)
        self.builder.cursor.comment("OP::less_than_or_equal_to END")

        return vari.Value(self.builder, CompilerType.create_from(res.type), res.get_reference(), True)