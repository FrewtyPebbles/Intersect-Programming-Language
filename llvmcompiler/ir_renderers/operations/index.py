from functools import lru_cache
from llvmcompiler.compiler_errors.comp_error import CompilerError
import llvmcompiler.compiler_types as ct
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.struct as st
from enum import Enum



indexes_type = list[ir.LoadInstr | ir.GEPInstr | ir.AllocaInstr | str | ir.Constant | ct.CompilerType | tuple[str, vari.Variable]]

        
class IndexOperation(Operation):
    def __init__(self, arguments: list[arg_type] = [], token = None) -> None:
        super().__init__(arguments, token)
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

        self.type = self.arguments[0].type

        for argument in self.arguments[1:]:
            processed_arg = self.process_arg(argument)
            indexes.append(processed_arg)
            if self.type.ptr_count > 1:
                self.type = self.type.deref_ptr()
            elif isinstance(self.type, ct.ArrayType):
                self.type = self.type.type
            


        

        pointer = self.gep(pointer, indexes)

        
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        if all([s in ptr.type._to_string() for s in "[x]"]):
            #print(f"\n\nARRAY INDS:\n\t{ptr}\nINDS:\n\t{indexes}")
            gep = self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])
            #print(f"\noriginal: {self.arguments[0].type}\nARRAY GEP SUCCESS, TYP: {self.type}")
            return gep
        else:
            #print(f"\nPTR INDS:\n\t{ptr}\nINDS:\n\t{indexes}")
            gep = self.builder.cursor.gep(ptr, [*indexes])
            #print(f"\noriginal: {self.arguments[0].type}\nPTR GEP SUCCESS, TYP: {self.type}")
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
    def __init__(self, arguments: list[arg_type] = [], token = None) -> None:
        super().__init__(arguments, token)
        self.ret_func:fn.FunctionDefinition = None
        self.type = None
        self.struct_operator = False

        
        
    def process_indexes(self):
        
        indexes:indexes_type = []
        # process all arguments to get indexes
        pointer = None
        if isinstance(self.arguments[0], vari.Variable):
            pointer = self.arguments[0].variable
        else:
            pointer = self.arguments[0].value
        self.type = self.arguments[0].type
        prev_struct:st.StructType = self.arguments[0].type

        virtual = False
        for argument in self.arguments[1:]:
            while isinstance(prev_struct, ct.Template):
                prev_struct = prev_struct.get_template_type()
            try:
                nxt = prev_struct.struct.get_attribute(argument.value, get_definition=True)
            except KeyError:
                prediction = None
                attrs = [*prev_struct.struct.attributes.keys(), *[fun.clean_name for fun in prev_struct.struct.struct_definition.functions]]
                if len(attrs) > 0:
                    similarity = [] # list of number of matching characters
                    for attr in attrs:
                        sim_level = 0
                        for user_char in argument.value:
                            sim_level += user_char in attr
                        similarity.append(sim_level)
                    prediction = f"did you mean '{attrs[similarity.index(max(similarity))]}'"

                CompilerError( self.token,
                        f"\"{argument.value}\" is not a valid attribute or function of struct {prev_struct}.",
                        hint=prediction
                    ).throw()

            if isinstance(nxt, fn.FunctionDefinition):
                self.ret_func = nxt
                break
            elif isinstance(nxt, tuple):
                # VTABLE
                if len(indexes) >= 1:
                    pointer = self.gep(pointer, indexes)
                indexes.append(nxt[0].get_value())

                vtable = self.builder.cursor.load(self.gep(pointer, indexes))

                self.ret_func = self.gep(vtable, [nxt[1].get_value()])

                virtual = True
                break
            else:
                #print(type(prev_struct))
                indexes.append(nxt.get_value())
                
                prev_struct = prev_struct.struct.raw_attributes[argument.value]
                
                while isinstance(prev_struct, ct.Template):
                    prev_struct = prev_struct.get_template_type()
        
            
        self.type = prev_struct.create_ptr()
        if not virtual:
            pointer = self.gep(pointer, indexes)

        
        self.type.parent = self.builder.function
        self.type.module = self.builder.module
        
        return pointer


    
    
    def gep(self, ptr:ir.Instruction, indexes:list):
        
        gep = self.builder.cursor.gep(ptr, [ir.IntType(32)(0), *indexes])

        return gep
        
            
    @lru_cache(32, True)
    def _write(self):
        self.builder.cursor.comment("OP::index START")
        self.arguments = self.get_variables()
        #print(f"ARGS {self.arguments}")
        res = self.process_indexes()
        self.builder.cursor.comment("OP::index END")

        #print(f"index = {res} {{{self.ret_func}}}")
        if self.ret_func == None:
            return vari.Value(self.type, res, True, self.arguments[0].heap, deref=True)
        else:
            return vari.Value(self.type, (res, self.ret_func), True, self.arguments[0].heap)
        