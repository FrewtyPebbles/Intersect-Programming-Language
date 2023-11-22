import llvmcompiler.compiler_types as ct
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.struct as st

indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | ct.CompilerType | tuple[str, vari.Variable]]

class IndexOperation(Operation):
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.ret_func:fn.FunctionDefinition = None
        self.type = None

    def process_indexes(self):


        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = self.arguments[0]
        prev_struct:st.StructType = pointer.type
        for argument in self.arguments[1:]:
            if isinstance(argument, int):
                indexes.append(ir.IntType(32)(argument))
            elif isinstance(argument, ct.LookupLabel):
                nxt = prev_struct.struct.get_attribute(argument.value, get_definition=True)
                if isinstance(nxt, fn.FunctionDefinition):
                    self.ret_func = nxt
                    break
                else:
                    indexes.append(nxt.get_value())
                    prev_struct = prev_struct.struct.raw_attributes[argument.value]
            else:
                indexes.append(self.process_arg(argument))

        self.type = prev_struct.create_ptr()
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return indexes

    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()

        indexes:indexes_type = self.process_indexes()

        
        if len(indexes):
            if self.arguments[0].heap:
                if isinstance(self.arguments[0], vari.Variable):
                    res = self.builder.cursor.gep(self.arguments[0].variable, indexes, True)
                elif isinstance(self.arguments[0], vari.Value):
                    res = self.builder.cursor.gep(self.arguments[0].value, indexes, True)
            else:
                if isinstance(self.arguments[0], vari.Variable):
                    
                    res = self.builder.cursor.gep(self.arguments[0].variable, [ir.IntType(32)(0), *indexes], True)
                if isinstance(self.arguments[0], vari.Value):
                    res = self.builder.cursor.gep(self.arguments[0].value, [ir.IntType(32)(0), *indexes], True)
            self.builder.cursor.comment("OP::index END")


            if self.ret_func == None:
                return vari.Value(self.type, res, True, self.arguments[0].heap)
            else:
                return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        else:
            self.builder.cursor.comment("OP::index END")
            if isinstance(self.arguments[0], vari.Variable):
                res = self.arguments[0].variable
            elif isinstance(self.arguments[0], vari.Value):
                res = self.arguments[0].value
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)