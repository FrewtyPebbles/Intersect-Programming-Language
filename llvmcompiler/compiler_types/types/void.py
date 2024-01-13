from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types.type as ct

class VoidType(ct.CompilerType):
    def __init__(self) -> None:
        self._size = 8
        self.value = ir.VoidType()
        self.name = "void"


    def cast_ptr(self):
        print("Error: cannot create a void pointer.")
