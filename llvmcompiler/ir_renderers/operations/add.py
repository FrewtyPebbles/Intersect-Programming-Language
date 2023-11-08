from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AddOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::add START")

        #process args
        arg1, arg2 = self.process_lhs_rhs_args()


        res:ir.Instruction = self.builder.cursor.add(arg1, arg2)

        self.builder.cursor.comment("OP::add END")

        return vari.Value(CompilerType.create_from(arg1.type), res.get_reference(), True)