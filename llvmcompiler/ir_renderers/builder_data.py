from __future__ import annotations

from typing import Dict, List, Union
from llvmlite import ir
from typing import TYPE_CHECKING
from .variable import Variable, Value
if TYPE_CHECKING:
    from .function import Function
import llvmcompiler.ir_renderers.operation as op
import sys

IS_64BIT = sys.maxsize > 2**32

SIZE_T = ir.IntType(1)
if IS_64BIT:
    SIZE_T = ir.IntType(64)
else:
    SIZE_T = ir.IntType(32)


class BuilderData:
    def __init__(self, scope:Function, builder:ir.IRBuilder, variables:List[Dict[str, Variable]]) -> None:
        self.scope = scope
        self.module = self.scope.module
        self.cursor = builder
        self.variables_stack = variables
        self.function = self.scope.function

        # this is where all function names/labels are defined
        self.functions = {
            # The key is the name that is parsed from source code,
            # the value is the llvm function.
            "print": self._std_printf(),
            "allocate": self._std_malloc(),
            "reallocate": self._std_realloc(),
            "deallocate": self._std_free()
            #"input":"input" # will be getting input function from c dll/so file via this method https://stackoverflow.com/questions/36658726/link-c-in-llvmlite
        }

    def declare_variable(self, variable:Variable):
        self.variables_stack[len(self.variables_stack)-1][variable.name] = variable

    def pop_variables(self):
        # frees all variables at the top of the stack/in the current scope and returns a list of the names of all freed variables
        top = self.variables_stack[len(self.variables_stack)-1]
        free_list:List[str] = []
        for name, var in top.items():
            if var.heap:
                self.scope.write_operation(op.Operation(op.OperationType.free_heap, [var]))
                free_list.append(name)
        self.variables_stack.pop()
        return free_list
        


    def set_variable(self, variable:Variable, value:Union[Variable, Value, any]):
        if variable.heap:
            print(f"(heap):setting value of:{variable.name}:to:{value.value}")
            if isinstance(value, Value):
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                temp_value = self.cursor.alloca(value.type.value)
                self.cursor.store(value.get_value(), temp_value)
                self.cursor.store(temp_value, variable.variable)
            elif isinstance(value, Variable):
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                self.cursor.store(value.load(), variable.variable)
            else:
                # This is for inline operations,  ir ordering is handled by LLVM
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                self.cursor.store(value, variable.variable)
        else:
            print(f"(stack):setting value of:{variable.name}:to:{value.value}")
            if isinstance(value, Value):
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                self.cursor.store(value.get_value(), variable.variable)
            elif isinstance(value, Variable):
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                self.cursor.store(value.load(), variable.variable)
            else:
                # This is for inline operations,  ir ordering is handled by LLVM
                self.variables_stack[len(self.variables_stack)-1][variable.name].value = value
                self.cursor.store(value, variable.variable)
        #print(str(self.cursor.module))

    def _get_variable(self, name:str) -> Variable:
        for layer_number, layer in enumerate(self.variables_stack):
            if name in layer.keys():
                return self.variables_stack[layer_number][name]
            

    # Standard library function declarations.
    def _std_printf(self) -> ir.Function:
        # this creates the IR for printf
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        return printf
    
    def _std_malloc(self) -> ir.Function:
        # this creates the IR for malloc
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(voidptr_ty, [SIZE_T], var_arg=False)
        malloc = ir.Function(self.module, printf_ty, name="malloc")
        return malloc
    
    def _std_free(self) -> ir.Function:
        # this creates the IR for malloc
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.VoidType(), [voidptr_ty], var_arg=False)
        free = ir.Function(self.module, printf_ty, name="free")
        return free
    
    def _std_realloc(self) -> ir.Function:
        # this creates the IR for malloc
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, SIZE_T], var_arg=False)
        realloc = ir.Function(self.module, printf_ty, name="realloc")
        return realloc