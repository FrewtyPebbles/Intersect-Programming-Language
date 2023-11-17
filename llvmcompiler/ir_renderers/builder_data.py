from __future__ import annotations

from typing import Dict, List, Union
from llvmlite import ir
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .function import Function
    import llvmcompiler.ir_renderers.scopes as scps
import llvmcompiler.ir_renderers.operations.free as fr
from llvmcompiler.ir_renderers.variable import Variable, Value
import sys


IS_64BIT = sys.maxsize > 2**32

SIZE_T = ir.IntType(1)
if IS_64BIT:
    SIZE_T = ir.IntType(64)
else:
    SIZE_T = ir.IntType(32)


class BuilderData:
    def __init__(self, function:Function, builder:ir.IRBuilder, variables:List[Dict[str, Variable]]) -> None:
        self.function = function
        self.module = self.function.module
        self.cursor = builder
        self.variables_stack = variables
        self.llvm_function = self.function.function
        self.debug = False
        self.scope_block_stack:List[Dict[str, ir.Block]] = []

        # this is where all function names/labels are defined
        self.functions = self.module.functions

    def declare_arguments(self):
        # declare the function arguments as variables
        for a_n, (arg_name, arg) in enumerate(self.function.arguments.items()):
            self.declare_variable(Variable(self, arg_name, Value(arg, self.function.function.args[a_n], is_instruction=True), function_argument = True))

    def clone_into_context(self, context:ir.Block):
        cpy = BuilderData(self.function, ir.IRBuilder(context), [])
        cpy.variables_stack = self.variables_stack
        cpy.scope_block_stack = self.scope_block_stack
        cpy.debug = self.debug
        return cpy

    def get_scope_block(self, name:str) -> Variable:
        for layer_number, layer in enumerate(self.scope_block_stack):
            if name in layer.keys():
                return self.scope_block_stack[layer_number][name]
    
    def pop_scope(self):
        self.scope_block_stack.pop()

    def declare_variable(self, variable:Variable):
        self.variables_stack[len(self.variables_stack)-1][variable.name] = variable
        return variable

    def append_scope(self, scope:scps.Scope):
        scope.builder = self
        return scope

    def push_scope(self, scope_blocks:Dict[str, ir.Block]):
        self.scope_block_stack.append(scope_blocks)

    def push_variable_stack(self):
        self.variables_stack.append({})

    def pop_variables(self):
        # frees all variables at the top of the stack/in the current scope and returns a list of the names of all freed variables
        top = self.variables_stack[len(self.variables_stack)-1]
        free_list:List[str] = []
        for name, var in top.items():
            if var.heap:
                free_op = self.function.create_operation(fr.FreeOperation([var]))
                free_op.write()
                free_list.append(name)
        self.variables_stack.pop()
        return free_list
    
    def write_operation(self, operation:fr.Operation):
        operation.builder = self
        return operation.write()
    
    def pop_heap(self):
        # frees heap variables at the top of the stack/in the current scope and returns a list of the names of all freed variables
        top = self.variables_stack[len(self.variables_stack)-1]
        free_list:List[str] = []
        for name, var in top.items():
            if var.heap:
                self.function.create_operation(fr.FreeOperation([var]))
                free_list.append(name)
                del top[name]
        return free_list
        


    def set_variable(self, variable:Variable, value:Union[Variable, Value, any]):
        if variable.heap:
            # print(f" - [(heap)] : setting value of : [{variable.name}] : to : [{value.value}]")
            if isinstance(value, Value):
                variable.value = value
                self.cursor.store(value.get_value(), variable.variable)
            elif isinstance(value, Variable):
                variable.value = value
                self.cursor.store(value, variable.variable)
            else:
                # This is for inline operations,  ir ordering is handled by LLVM
                variable.value = value
                self.cursor.store(value, variable.variable)
        else:
            # print(f" - [(stack)] : setting value of : [{variable.name}] : to : [{value.value}]")
            if isinstance(value, Value):
                variable.value = value
                self.cursor.store(value.get_value(), variable.variable)
            elif isinstance(value, Variable):
                variable.value = value
                self.cursor.store(value.load(), variable.variable)
            else:
                # This is for inline operations,  ir ordering is handled by LLVM
                variable.value = value
                self.cursor.store(value, variable.variable)
        return variable

    def get_variable(self, name:str) -> Variable:

        for layer_number, layer in enumerate(self.variables_stack):
            if name in layer.keys():
                return self.variables_stack[layer_number][name]
        print(f"Error: Variable \"{name}\" not in reference stack:\n{self.variables_stack}")
    
    def alloca(self, ir_type:ir.Type, size:int = None, name = ""):
        entry_block = self.function.entry
        curr_block = self.cursor.block
        self.cursor.position_at_start(entry_block)
        alloca_instr = self.cursor.alloca(ir_type, size, name)
        self.cursor.position_at_end(curr_block)
        return alloca_instr