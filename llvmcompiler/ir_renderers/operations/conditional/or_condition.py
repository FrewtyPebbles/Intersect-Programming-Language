import llvmcompiler.compiler_types as ct
from ...operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class OrOperation(Operation):
    def __init__(self, arguments: list = None, token = None) -> None:
        super().__init__(arguments, token=token)
        self.op_token = "or"

    def _write(self):
        self.builder.cursor.comment("OP::or START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
        
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.or_(arg1, arg2)
        self.builder.cursor.comment("OP::or END")

        return vari.Value(ct.BoolType(), res, True)