from ..operation import Operation
from llvmlite import ir

class FreeOperation(Operation):
    def _write(self):
        self.builder.cursor.comment(" OP::free(heap) START")
        self.arguments = self.get_variables()
        voidptr_ty = ir.IntType(8).as_pointer()
        ptr = self.builder.cursor.gep(self.arguments[0].variable, [ir.IntType(8)(0)], inbounds=True)
        # dbg_llvm_print(self.builder, ptr)
        bc = self.builder.cursor.bitcast(ptr, voidptr_ty)
        self.builder.cursor.call(self.builder.functions["deallocate"].get_function().function, [bc])
        self.builder.cursor.comment(" OP::free(heap) END")