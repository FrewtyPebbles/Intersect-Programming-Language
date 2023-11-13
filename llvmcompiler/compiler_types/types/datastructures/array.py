from llvmlite import ir
from typing import TYPE_CHECKING
import llvmcompiler.compiler_types as ct

# Array
class ArrayType(ct.CompilerType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type

    @property    
    def size(self):
        return self.type.size * self.count
        
    @property
    def value(self):
        return ir.ArrayType(self.type.value, self.count)

    def render_template(self):
        self.type.parent = self.parent
        self.type.render_template()
        return

    def get_type(self):
        return self.type

    def cast_ptr(self):
        return ArrayPointerType(self.type, self.count)
    
class ArrayPointerType(ArrayType):
    def __init__(self, item_type:ct.CompilerType, count:int) -> None:
        self.count = count
        self.type = item_type
        self._size = self.type.size * self.count
        self.value = ir.ArrayType(self.type.value, self.count).as_pointer()