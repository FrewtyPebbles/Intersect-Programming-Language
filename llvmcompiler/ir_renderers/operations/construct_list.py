from llvmcompiler.compiler_types.type import CompilerType
from llvmcompiler.compiler_types.types.datastructures.array import ArrayType
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition
from llvmcompiler.ir_renderers.struct import StructType

class ConstructListOperation(Operation):
    """
    This is used to construct lists.
    """
    def __init__(self, item_type:CompilerType, arguments: list[arg_type] = [], heap = False) -> None:
        super().__init__(arguments)
        self.type = item_type
        self.heap = heap

    def create_list(self):
        self.type.module = self.builder.module
        self.type.parent = self.builder.function
        self.type.builder = self.builder
        for indn, ind in enumerate(self.arguments):
            self.arguments[indn].parent = self.builder.function
            self.arguments[indn].builder = self.builder
            self.arguments[indn].module = self.builder.module
            self.arguments[indn] = self.process_arg(ind)
        
        

    def _write(self):
        self.builder.cursor.comment("OP::construct:list START")
        # cast the arguments
        self.create_list()

        list_alloca = self.builder.alloca(ir.ArrayType(self.type.value, len(self.arguments)))
        for item_n, item in enumerate(self.arguments):
            pointer = self.builder.cursor.gep(list_alloca, [ir.IntType(32)(0), ir.IntType(32)(item_n)])
            self.builder.module.dbg_print()
            print(item)
            self.builder.cursor.store(item, pointer)

        

        self.builder.cursor.comment("OP::construct:list end")
        if self.heap:
            ret = vari.HeapValue(ArrayType(self.type, len(self.arguments)), self.builder.cursor.load(list_alloca), True)
            ret.parent = self.builder.function
            ret.builder = self.builder
            ret.module = self.builder.module
            ret.render_heap()
            return ret
        else:
            ret = vari.Value(ArrayType(self.type, len(self.arguments)), self.builder.cursor.load(list_alloca), True)
            ret.parent = self.builder.function
            ret.builder = self.builder
            ret.module = self.builder.module
            return ret