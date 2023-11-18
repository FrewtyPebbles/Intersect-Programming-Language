from ..operation import Operation
from llvmlite import ir

class FreeOperation(Operation):
    def _write(self):
        self.builder.cursor.comment(" OP::free(heap) START")
        self.arguments = self.get_variables()
        voidptr_ty = ir.IntType(8).as_pointer()
        ptr = None
        if hasattr(self.arguments[0], "variable"):
            ptr = self.builder.cursor.gep(self.arguments[0].variable, [ir.IntType(8)(0)], inbounds=True)
        else:
            ptr = self.builder.cursor.gep(self.arguments[0], [ir.IntType(8)(0)], inbounds=True)


        bc = self.builder.cursor.bitcast(ptr, voidptr_ty)
        self.builder.cursor.call(self.builder.functions["libc_free"].get_function().function, [bc])
        self.builder.cursor.comment(" OP::free(heap) END")