from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DereferenceOperation(Operation):
    def __init__(self, arguments: list = None, token = None) -> None:
        super().__init__(arguments, token)
        self.op_token = "$"
        self.struct_operator = False
    def write(self):
        #print(f"DEREF {self.arguments}")
        return super().write()
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::dereference START")
        self.arguments = self.get_variables()
        
        res = self.arguments[0].load()
        
        self.builder.cursor.comment("OP::dereference END")
        deref = not self.arguments[0].function_argument if hasattr(self.arguments[0], "function_argument") else True
        return vari.Value(self.arguments[0].type.create_deref(), res, True, deref = deref)