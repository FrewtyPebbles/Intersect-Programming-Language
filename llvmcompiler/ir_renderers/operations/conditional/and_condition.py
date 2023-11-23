from llvmcompiler.compiler_types.type import CompilerType
from ...operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AndOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::and START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.and_(arg1, arg2)
        self.builder.cursor.comment("OP::and END")

        return vari.Value(CompilerType.create_from(res.type), res.get_reference(), True)