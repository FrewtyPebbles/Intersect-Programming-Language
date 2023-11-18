from __future__ import annotations
from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct
if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.struct as st
    import llvmcompiler.ir_renderers.function as fn

# I32
class LookupLabel(ct.CompilerType):
    """
    This is used to lookup struct attrubutes with the `.` operator.
    """
    def __init__(self, name:str) -> None:
        super().__init__()
        self.value = name