from llvmcompiler.compiler_types.type import CompilerType
from ...operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class OrOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::or START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.or_(arg1, arg2)
        self.builder.cursor.comment("OP::or END")

        return vari.Value(CompilerType.create_from(res.type, self.builder.module, self.builder.function), res, True)