import llvmcompiler.compiler_types as ct
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.struct as st
from enum import Enum

indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | ct.CompilerType | tuple[str, vari.Variable]]

#TODO:
#
# - Make a separate gep instruction whenever the next index is for a non struct type
#

class IndType(Enum):
    Struct = 1
    Array = -1
    Unknown = 0

class IndexOperation(Operation):
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.ret_func:fn.FunctionDefinition = None
        self.type = None
        

    def process_indexes(self):


        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value
        prev_struct:st.StructType = self.arguments[0].type
        is_struct = IndType.Struct if isinstance(self.arguments[0].type, st.StructType) else IndType.Array
        step_over_ptr = isinstance(self.arguments[0].type, st.StructType)

        #print(f"INDEX ARGS {self.arguments}")
        for argument in self.arguments[1:]:
            if isinstance(argument, int):
                indexes.append(ir.IntType(32)(argument))
            elif isinstance(argument, ct.LookupLabel):
                if is_struct in {IndType.Unknown, IndType.Array}:
                    if is_struct == IndType.Array:
                        pointer = self.gep(pointer, indexes, step_over_ptr)
                        indexes = []
                        step_over_ptr = True
                    is_struct = IndType.Struct

                nxt = prev_struct.struct.get_attribute(argument.value, get_definition=True)

                if isinstance(nxt, fn.FunctionDefinition):
                    self.ret_func = nxt
                    break
                else:
                    indexes.append(nxt.get_value())
                    prev_struct = prev_struct.struct.raw_attributes[argument.value]
            else:
                # for [] operations
                if is_struct == IndType.Struct:
                    pointer = self.gep(pointer, indexes, step_over_ptr)
                    indexes = []
                    is_struct = IndType.Array
                    step_over_ptr = False

                #print(f"ARGU = {argument}")
                processed_arg = self.process_arg(argument)
                #print(f"PROCESSED ARGU = {processed_arg}")
                indexes.append(processed_arg)

        pointer = self.gep(pointer, indexes, step_over_ptr)

        self.type = prev_struct.create_ptr()
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer

    def cast_itter_i32(self, itter:list[ir.IntType]):
        for i_n, item in enumerate(itter):
            if item != ir.IntType(32):
                try:
                    itter[i_n] = self.builder.cursor.bitcast(item, ir.IntType(32))
                except RuntimeError:
                    print("Error: Cannot use i-type larger than 32 within the index operator.")
    
    def gep(self, ptr:ir.Instruction, indexes:list, step_over_pointer = True):
        if step_over_pointer:
            #print(ptr)
            #print(indexes)
            return self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
        else:
            #print(indexes)
            return self.builder.cursor.gep(ptr, [*indexes])
        
            

    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")


        if self.ret_func == None:
            return vari.Value(self.type, res, True, self.arguments[0].heap)
        else:
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        