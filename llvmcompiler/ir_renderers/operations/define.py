from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.struct as st

class DefineOperation(Operation):
    def __init__(self, arguments: list[arg_type] = None, force_type:ct.CompilerType = None) -> None:
        super().__init__(arguments)
        self.force_type = force_type
        self.struct_operator = False
    def _write(self):

        self.builder.cursor.comment("OP::define(stack) START")
        
        self.arguments[1].parent = self.builder.function
        self.arguments[1].module = self.builder.module
        typ = self.arguments[1].type
        if self.force_type != None:
            typ = self.arguments[1].type = self.force_type
        elif typ.is_pointer:
            self.force_type = typ
            self.arguments[1].type = typ.create_deref()
            
        
        #print(self.arguments)
        var = self.builder.declare_variable(vari.Variable(self.builder, *self.arguments))
        
        if isinstance(typ, st.StructType) and len(typ.struct.vtable_functions) > 0:
            vtable = self.builder.cursor.gep(var.variable, [ir.IntType(32)(0), typ.struct.attributes["META__VTABLE"].get_value()])
            
            self.builder.cursor.store(typ.struct.vtable_global, vtable)
        
        self.builder.cursor.comment("OP::define(stack) END")
        return var