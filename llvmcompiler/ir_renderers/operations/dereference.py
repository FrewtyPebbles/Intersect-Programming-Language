from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class DereferenceOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::dereference START")
        self.arguments = self.get_variables()
        #process arg1
        if not isinstance(self.arguments[0], vari.Variable):
            # throw error because the supplied token/item is not dereferenceable
            print(f"Error: {self.arguments[0]} cannot be dereferenced.")
        res = self.arguments[0].load()
        
        self.builder.cursor.comment("OP::dereference END")

        return vari.Value(CompilerType.create_from(res.type), res, True)