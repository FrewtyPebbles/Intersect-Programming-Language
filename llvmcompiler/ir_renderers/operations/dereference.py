from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DereferenceOperation(Operation):
    def __init__(self, arguments: list = None) -> None:
        super().__init__(arguments)
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
        return vari.Value(CompilerType.create_from(res.type, self.builder.module, self.builder.function), res, True, deref = deref)