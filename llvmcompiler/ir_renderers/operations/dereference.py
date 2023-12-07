from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DereferenceOperation(Operation):
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::dereference START")
        self.arguments = self.get_variables()
        #process arg1
        res = self.arguments[0].load()
        
        self.builder.cursor.comment("OP::dereference END")

        return vari.Value(CompilerType.create_from(res.type, self.builder.module, self.builder.function), res, True)