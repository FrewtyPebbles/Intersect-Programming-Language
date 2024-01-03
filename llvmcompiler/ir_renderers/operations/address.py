from functools import lru_cache
from llvmcompiler.compiler_types.type import CompilerType
from llvmcompiler.ir_renderers.operation import arg_type
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class AddressOperation(Operation):
    def __init__(self, arguments: list[arg_type] = None) -> None:
        super().__init__(arguments)
        self.struct_operator = False
    
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::address START")
        self.arguments = self.get_variables()
        res = None
        if isinstance(self.arguments[0], vari.Value):
            res = self.arguments[0].get_value(True)
            #self.builder.module.dbg_print()
        else:
            res = self.arguments[0].variable
        self.builder.cursor.comment("OP::address END")
        return vari.Value(self.arguments[0].type.cast_ptr(), res, True, address = True)