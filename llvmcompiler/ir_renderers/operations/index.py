from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | CompilerType | tuple[str, vari.Variable]]

class IndexOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        indexes:indexes_type = []
        # process all arguments to get indexes
        for argument in self.arguments[1:]:
            indexes.append(self.process_arg(argument))
        if self.arguments[0].heap:
            if isinstance(self.arguments[0], vari.Variable):
                res = self.builder.cursor.gep(self.arguments[0].variable, indexes)
            elif isinstance(self.arguments[0], vari.Value):
                res = self.builder.cursor.gep(self.arguments[0].value, indexes)
        else:
            if isinstance(self.arguments[0], vari.Variable):
                res = self.builder.cursor.gep(self.arguments[0].variable, [ir.IntType(32)(0), *indexes])
            if isinstance(self.arguments[0], vari.Value):
                res = self.builder.cursor.gep(self.arguments[0].value, [ir.IntType(32)(0), *indexes])
        self.builder.cursor.comment("OP::index END")

        return vari.Value(CompilerType.create_from(res.type), res, True, self.arguments[0].heap)