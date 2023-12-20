from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AddressOperation(Operation):
    def write(self):
        #print(f"ADDRESS OP {self.arguments}")
        return super().write()
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::address START")
        self.arguments = self.get_variables()
        res = None
        if isinstance(self.arguments[0], vari.Value):
            res = self.arguments[0].value
            #self.builder.module.dbg_print()
        else:
            res = self.arguments[0].variable
        self.builder.cursor.comment("OP::address END")
        return vari.Value(CompilerType.create_from(res.type, self.builder.module, self.builder.function), res, True, address = True)