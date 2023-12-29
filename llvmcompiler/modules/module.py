from __future__ import annotations
from functools import lru_cache

from llvmlite.ir.context import global_context
import llvmcompiler.ir_renderers.function as fn
from llvmlite import ir
import llvmcompiler.compiler_types as ty
import llvmcompiler.ir_renderers.builder_data as bd
import llvmcompiler.ir_renderers.struct as st
from typing import Dict, List, Union

class Module:
    def __init__(self, name:str = '', scope:list[fn.FunctionDefinition | st.StructDefinition] = None, mangle_salt = "MMAANNGGLLEE") -> None:
        self.name = name
        self.module = ir.Module(name=name)
        self.functions:Dict[str, ir.Function | fn.FunctionDefinition] = {
            # The key is the name that is parsed from source code,
            # the value is the llvm function.
            "libc_printf": fn.CFunctionDefinition(self._std_printf()),
            "libc_malloc": fn.CFunctionDefinition(self._std_malloc()),
            "libc_realloc": fn.CFunctionDefinition(self._std_realloc()),
            "libc_memcpy": fn.CFunctionDefinition(self._std_memcpy()),
            "libc_free": fn.CFunctionDefinition(self._std_free()),
            "libc_putchar": fn.CFunctionDefinition(self._std_putchar()),
            "libc_getchar": fn.CFunctionDefinition(self._std_getchar())
            #"input":"input" # will be getting input function from c dll/so file via this method https://stackoverflow.com/questions/36658726/link-c-in-llvmlite
        }
        self.structs:dict[str, st.StructDefinition] = {}
        self.scope = [] if scope == None else scope
        self.mangle_salt = mangle_salt
        
        self.null = ir.GlobalVariable(self.module, ir.IntType(8), "null")
        """
        Point a value to this when it is freed
        """
        self.null.initializer = ir.IntType(8)(ord("\0"))

        self.mangled_members:set[str] = set()

    def get_documentation(self):
        ret_val = f"<div><h1>{self.name}</h1>"
        for interface in self.scope:
            ret_val += interface.get_documentation()

        ret_val += "</div>"
        return ret_val
    
    def write(self):
        for scope_line in self.scope:
            if isinstance(scope_line, fn.FunctionDefinition):
                self.append_function(scope_line)
                if scope_line.name == "main" or scope_line.extern:
                    scope_line.get_function()
            elif isinstance(scope_line, st.StructDefinition):
                self.append_struct(scope_line)

    @lru_cache(32, True)
    def get_struct(self, name:str):
        """
        When checking "label" type names in the syntax tree builder, this is the function you should call.
        If the function returns None, then the struct does not exist so throw an error.
        """
        
        if name in self.structs.keys():
            return self.structs[name]
        else:
            return None

    def append_struct(self, struct:st.StructDefinition):
        struct.module = self
        self.structs[struct.name] = struct
        return struct


    def append_function(self, function:fn.FunctionDefinition) -> fn.FunctionDefinition:
        function.module = self
        self.functions[function.name] = function
        return function
    
    def dbg_print(self):
        """
        Prints the current state of the rendered IR for the module.
        """
        print(self.module)

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
    
    def _std_memcpy(self) -> ir.Function:
        # this creates the IR for malloc
        voidptr_ty = ir.IntType(8).as_pointer()
        memcpy_ty = ir.FunctionType(ir.VoidType(), [voidptr_ty, voidptr_ty, bd.SIZE_T], var_arg=False)
        realloc = ir.Function(self.module, memcpy_ty, name="memcpy")
        return realloc
    
    def _std_realloc(self) -> ir.Function:
        # this creates the IR for realloc
        voidptr_ty = ir.IntType(8).as_pointer()
        realloc_ty = ir.FunctionType(voidptr_ty, [voidptr_ty, bd.SIZE_T], var_arg=False)
        realloc = ir.Function(self.module, realloc_ty, name="realloc")
        return realloc

    def _std_putchar(self) -> ir.Function:
        # this creates the IR for putchar
        char_ty = ir.IntType(8)
        realloc_ty = ir.FunctionType(char_ty, [char_ty], var_arg=False)
        realloc = ir.Function(self.module, realloc_ty, name="putchar")
        return realloc
    
    def _std_getchar(self) -> ir.Function:
        # this creates the IR for putchar
        char_ty = ir.IntType(8)
        realloc_ty = ir.FunctionType(char_ty, [], var_arg=False)
        realloc = ir.Function(self.module, realloc_ty, name="getchar")
        return realloc
    