from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class SubtractOperation(Operation):
    def __init__(self, arguments: list = None) -> None:
        super().__init__(arguments)
        self.op_token = "-"
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::subtract START")
        self.arguments = self.get_variables()
        self.convert_literal_types()
            
        #process args
        arg1, arg2 = self.process_lhs_rhs_args()

        res:ir.Instruction = self.builder.cursor.sub(arg1, arg2)
        self.builder.cursor.comment("OP::subtract END")

        return vari.Value(self.arguments[0].type, res, True)