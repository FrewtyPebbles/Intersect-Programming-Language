from __future__ import annotations

from typing import Dict, List, Union
from llvmlite import ir
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .function import Function
    import llvmcompiler.ir_renderers.scopes as scps
import llvmcompiler.ir_renderers.operations.free as fr
from llvmcompiler.ir_renderers.variable import Variable, Value, HeapValue
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
        self.value_heap_stack:list[list[ir.Instruction]] = [[]]
        self.llvm_function = self.function.function
        self.debug = False
        self.scope_block_stack:List[Dict[str, ir.Block]] = []

        self.memory_stack:list[MemoryStackFrame] = [MemoryStackFrame(self.function)]

        

        # this is where all function names/labels are defined
        self.functions = self.module.functions

    @property
    def memory_top(self):
        return self.memory_stack[len(self.memory_stack)-1]

    @property
    def variable_top(self):
        return self.memory_top.variable_top
    
    @property
    def value_top(self):
        return self.memory_top.value_top

    def declare_arguments(self):
        # declare the function arguments as variables
        for a_n, (arg_name, arg) in enumerate(self.function.arguments.items()):
            self.memory_top.declare_variable(Variable(self, arg_name, Value(arg, self.function.function.args[a_n], is_instruction=True), function_argument = True))

    def clone_into_context(self, context:ir.Block):
        cpy = BuilderData(self.function, ir.IRBuilder(context), [])
        cpy.variables_stack = self.variables_stack
        cpy.scope_block_stack = self.scope_block_stack
        cpy.debug = self.debug
        return cpy
    

            
    def break_scope(self) -> Variable:
        return self.memory_top.break_block()
    
    def pop_scope(self):
        self.memory_stack.pop()

    def declare_variable(self, variable:Variable):
        return self.memory_top.declare_variable(variable)
    
    def push_value_heap(self, malloc:ir.Instruction):
        return self.memory_top.push_value_heap(malloc)

    def append_scope(self, scope:scps.Scope):
        scope.builder = self
        return scope

    def push_scope(self, exit_block:ir.Block):
        self.memory_stack.append(MemoryStackFrame(self.function, exit_block))

    def push_variable_stack(self):
        self.memory_top.push_variable_stack()

    def pop_variables(self):
        return self.memory_top.pop_variables()
    
    def write_operation(self, operation:fr.Operation):
        operation.builder = self
        return operation.write()
    
    def pop_heap(self):
        return self.memory_top.pop_heap()
        


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
            if isinstance(value, HeapValue):
                variable.value = value
                if not value.is_instruction:
                    self.cursor.store(value.get_value(), variable.variable)
            elif isinstance(value, Value):
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
        for layer in reversed(self.memory_stack):
            var = layer.get_variable(name)
            if var == None:
                continue
            return var
        print(f"Error: Variable \"{name}\" not in reference stack:\n{self.variables_stack}")
    
    def alloca(self, ir_type:ir.Type, size:int = None, name = ""):
        entry_block = self.function.entry
        curr_block = self.cursor.block
        self.cursor.position_at_start(entry_block)
        alloca_instr = self.cursor.alloca(ir_type, size, name)
        self.cursor.position_at_end(curr_block)
        return alloca_instr
    
class MemoryStackFrame:
    """
    This class creates a new stack for memory each time a `break`-able scope is pushed to the execution context.
    
    When a break is called, everything on the variable stack is garbage collected.

    When A MemoryStackFrame is poped from self.memory_stack in the builder data, the `__del__` dunder is called
    which frees all of the memory on that stack frame.
    """
    def __init__(self, function:Function, exit_block:ir.Block = None) -> None:
        self.variables_stack:list[dict[str, Variable]] = [{}]
        self.value_heap_stack:list[list[ir.Instruction]] = [[]]
        self.exit:ir.Block = exit_block
        self.function = function

    @property
    def variable_top(self):
        return self.variables_stack[len(self.variables_stack)-1]
    
    @property
    def value_top(self):
        return self.value_heap_stack[len(self.value_heap_stack)-1]

    def push_variable_stack(self):
        self.variables_stack.append({})
        self.value_heap_stack.append([])
    
    def pop_heap(self):
        # frees heap variables at the top of the stack/in the current scope and returns a list of the names of all freed variables
        top = self.variable_top
        free_list:List[str] = []
        for name, var in top.items():
            if var.heap:
                self.function.create_operation(fr.FreeOperation([var]))
                free_list.append(name)
                del top[name]
        return free_list
    
    def break_block(self) -> ir.Block:

        #first free and remove the memory in the current scope
        for key, var in self.variable_top.items():
            if var.heap:
                free_op = self.function.create_operation(fr.FreeOperation([var]))
                free_op.write()
                del self.variables_stack[len(self.variables_stack)-1][key]

        for ind, ins in enumerate(self.value_heap_stack[len(self.value_heap_stack)-1]):
            free_op = self.function.create_operation(fr.FreeOperation([ins]))
            free_op.write()
            self.value_heap_stack[len(self.value_heap_stack)-1].pop(ind)


        # then free everything we're gonna be breaking out of

        for v_stack in reversed(self.variables_stack):
            for var in v_stack.values():
                if var.heap:
                    free_op = self.function.create_operation(fr.FreeOperation([var]))
                    free_op.write()

        
        for v_h_stack in reversed(self.value_heap_stack):
            for ins in v_h_stack:
                free_op = self.function.create_operation(fr.FreeOperation([ins]))
                free_op.write()
    
        return self.exit

    def get_variable(self, name:str) -> Variable | None:
        for layer in reversed(self.variables_stack):
            if name in layer.keys():
                return layer[name]
        return None

    def push_value_heap(self, malloc:ir.Instruction):
        self.value_top.append(malloc)
        return malloc
        
    
    def declare_variable(self, variable:Variable):
        self.variable_top[variable.name] = variable
        return variable

    def pop_variables(self):
        # frees all variables at the top of the stack/in the current scope and returns a list of the names of all freed variables
        # old garbage collector
        top = self.variable_top
        free_list:List[str] = []
        for name, var in top.items():
            if var.heap:
                free_op = self.function.create_operation(fr.FreeOperation([var]))
                free_op.write()
                free_list.append(name)
        self.variables_stack.pop()

        # new garbage collector
        val_top = self.value_top
        for ins in val_top:
            free_op = self.function.create_operation(fr.FreeOperation([ins]))
            free_op.write()
        self.value_heap_stack.pop()

        return free_list

    def __del__(self):
        self.variables_stack.reverse()
        for v_stack in self.variables_stack:
            for name, var in v_stack.items():
                if var.heap:
                    free_op = self.function.create_operation(fr.FreeOperation([var]))
                    free_op.write()

        self.value_heap_stack.reverse()
        for v_h_stack in self.value_heap_stack:
            for ins in v_h_stack:
                free_op = self.function.create_operation(fr.FreeOperation([ins]))
                free_op.write()
