from llvmcompiler.ir_renderers.function import Function
from llvmlite import ir
import llvmcompiler.compiler_types.type as ty
import llvmcompiler.ir_renderers.builder_data as bd
from typing import Dict, List, Union


class Module:
    def __init__(self, name:str = '') -> None:
        self.module = ir.Module(name=name)
        self.functions:Dict[str, ir.Function] = {
            # The key is the name that is parsed from source code,
            # the value is the llvm function.
            "print": self._std_printf(),
            "allocate": self._std_malloc(),
            "reallocate": self._std_realloc(),
            "deallocate": self._std_free()
            #"input":"input" # will be getting input function from c dll/so file via this method https://stackoverflow.com/questions/36658726/link-c-in-llvmlite
        }

    def create_function(self, name:str, arguments:Dict[str, ty.AnyType], return_type:ty.AnyType, variable_arguments = False) -> Function:
        func = Function(self, name, arguments, return_type, variable_arguments)
        self.functions[name] = func.function
        return func

    def __repr__(self) -> str:
        return f"{self.module}"
    
    def __str__(self) -> str:
        return f"{self.module}"
    
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
        printf_ty = ir.FunctionType(voidptr_ty, [bd.SIZE_T], var_arg=False)
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
        printf_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, bd.SIZE_T], var_arg=False)
        realloc = ir.Function(self.module, printf_ty, name="realloc")
        return realloc