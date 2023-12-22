from functools import lru_cache
import llvmcompiler.compiler_types as ct
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.struct as st
from enum import Enum

indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | ct.CompilerType | tuple[str, vari.Variable]]

        
class IndexOperation(Operation):
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.type = None
        self.op_token = "[]"
        
    def process_indexes(self):

        #print(f"\nINDEX = {self.arguments}")
        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value

        for argument in self.arguments[1:]:
            processed_arg = self.process_arg(argument)
            indexes.append(processed_arg)


        

        pointer = self.gep(pointer, indexes)

        
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        if all([s in ptr.type._to_string() for s in "[x]"]):
            #print(f"\n\nARRAY INDS:\n\t{ptr}\nINDS:\n\t{indexes}")
            gep = self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
            self.type = ct.CompilerType.create_from(gep.type, self.builder.module, self.builder.function)
            #print(f"\nARRAY GEP SUCCESS, TYP: {self.type}")
            return gep
        else:
            #print(f"\nPTR INDS:\n\t{ptr}\nINDS:\n\t{indexes}")
            gep = self.builder.cursor.gep(ptr, [*indexes])
            self.type = ct.CompilerType.create_from(gep.type, self.builder.module, self.builder.function)
            #print(f"\nPTR GEP SUCCESS, TYP: {self.type}")
            return gep
            
        
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")

        #print(f"ind_type = {self.type}")
        return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        
class AccessOperation(Operation):
    "This is for indexing structs with the . or -> operator"
    def __init__(self, arguments: list[arg_type] = []) -> None:
        super().__init__(arguments)
        self.ret_func:fn.FunctionDefinition = None
        self.type = None
        self.struct_operator = False
        
        
    def process_indexes(self):

        #print(f"\nACCESS = {self.arguments}")
        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value
        prev_struct:st.StructType = self.arguments[0].type
        for argument in self.arguments[1:]:
            if isinstance(prev_struct, ct.Template):
                prev_struct = prev_struct.get_template_type()
            nxt = prev_struct.struct.get_attribute(argument.value, get_definition=True)
            
            
            if isinstance(nxt, fn.FunctionDefinition):
                self.ret_func = nxt
                break
            else:
                indexes.append(nxt.get_value())
                prev_struct = prev_struct.struct.raw_attributes[argument.value]
                

        pointer = self.gep(pointer, indexes)

        
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        gep = self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
        self.type = ct.CompilerType.create_from(gep.type, self.builder.module, self.builder.function)
        return gep
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        #print(f"ARGS {self.arguments}")
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")

        #print(f"acc_type = {self.type} {{{self.arguments}}}")
        if self.ret_func == None:
            return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        else:
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        