import llvmcompiler.compiler_types.type as ct
import llvmcompiler.ir_renderers.operation as op
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class EqualToOperation(op.Operation):
    def _write(self):
        self.builder.cursor.comment("OP::equal_to START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.icmp_signed('==', arg1, arg2)
        self.builder.cursor.comment("OP::equal_to END")

        return vari.Value(ct.CompilerType.create_from(res.type), res.get_reference(), True)