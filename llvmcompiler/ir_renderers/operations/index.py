from functools import lru_cache
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
# - This needs to be reworked badly to be less bug prone.
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

        #print(self.arguments)
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
                
                p_struct = None

                if isinstance(prev_struct, ct.ArrayType):
                    p_struct = prev_struct.type
                else:
                    p_struct = prev_struct
                if isinstance(p_struct, ct.Template):
                    p_struct = p_struct.get_template_type()
                
                nxt = p_struct.struct.get_attribute(argument.value, get_definition=True)
                
                
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

                if isinstance(prev_struct, ct.ArrayType):
                    prev_struct = prev_struct.type
                    step_over_ptr = True
                #print(f"ARGU = {argument}")
                processed_arg = self.process_arg(argument)
                #print(f"PROCESSED ARGU = {processed_arg}")
                indexes.append(processed_arg)

        pointer = self.gep(pointer, indexes, step_over_ptr)

        self.type = prev_struct.create_ptr()
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list, step_over_pointer = True):
        if step_over_pointer:
            return self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
        else:
            return self.builder.cursor.gep(ptr, [*indexes])
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")


        if self.ret_func == None:
            return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        else:
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        
class NewIndexOperation(Operation):
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.type = None
        
    def process_indexes(self):

        print(f"\nINDEX = {self.arguments}")
        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value
        prev_type = self.arguments[0].type

        #print(f"INDEX ARGS {self.arguments}")
        for argument in self.arguments[1:]:
                
            if prev_type.is_pointer:
                prev_type = prev_type.create_deref()
                print(f"PTR {prev_type}")
            elif isinstance(prev_type, ct.ArrayType):
                prev_type = prev_type.type
                print(f"ARRAY {prev_type}")
            else:
                print("Error: Cannot index scalar type.")
            processed_arg = self.process_arg(argument)
            
            indexes.append(processed_arg)


        self.type = prev_type
        print(f"ind_type = {self.type}")

        pointer = self.gep(pointer, indexes)

        
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        if isinstance(ptr.type, ir.ArrayType):
            print(f"ARRAY INDS:\n{ptr}\nINDS:\n{indexes}")
            return self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
        else:
            print(f"PTR INDS:\n{ptr}\nINDS:\n{indexes}")
            return self.builder.cursor.gep(ptr, [*indexes])
        
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")


        return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        
class AccessOperation(Operation):
    "This is for indexing structs with the . or -> operator"
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.ret_func:fn.FunctionDefinition = None
        self.type = None
        
    def process_indexes(self):

        print(f"\nACCESS = {self.arguments}")
        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value
        prev_struct:st.StructType = self.arguments[0].type
        self.type = prev_struct
        #print(f"INDEX ARGS {self.arguments}")
        for argument in self.arguments[1:]:
            p_struct = prev_struct
            if isinstance(p_struct, ct.Template):
                p_struct = p_struct.get_template_type()
            
            nxt = p_struct.struct.get_attribute(argument.value, get_definition=True)
            
            
            if isinstance(nxt, fn.FunctionDefinition):
                self.ret_func = nxt
                break
            else:
                indexes.append(nxt.get_value())
                prev_struct = prev_struct.struct.raw_attributes[argument.value]
                self.type = prev_struct
                

        pointer = self.gep(pointer, indexes)

        print(f"acc_type = {self.type}")
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        
        return self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")


        if self.ret_func == None:
            return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        else:
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        