from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.compiler_types as ct

indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | CompilerType | tuple[str, vari.Variable]]

class AccessOperation(Operation):
    """
    Goes through the labels being accessed and returns either a tuple[ir.Function, Struct] if it is a function,
    or a pointer to some value.
    """

    def _write(self) -> tuple[ir.Function, ct.Struct] | ir.GEPInstr:
        self.is_function = False
        self.final_item_heap = False
        self.builder.cursor.comment("OP::index START")

        
        res = None
        self.builder.cursor.comment("OP::index END")

        return vari.Value(CompilerType.create_from(res.type), res, True, self.final_item_heap)