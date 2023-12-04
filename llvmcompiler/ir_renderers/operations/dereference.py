from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DereferenceOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::dereference START")
        self.arguments = self.get_variables()
        #process arg1
        print(self.arguments[0])
        res = self.arguments[0].load()
        
        self.builder.cursor.comment("OP::dereference END")

        return vari.Value(CompilerType.create_from(res.type), res, True)