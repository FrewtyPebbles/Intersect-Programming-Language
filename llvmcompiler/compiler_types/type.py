from __future__ import annotations
from llvmlite import ir
from copy import deepcopy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import llvmcompiler.modules.module as md

class CompilerType:
    """
    This class is inherited by all type classes.
    """

    
    _size:int
    value:ir.Type
    parent: None
    module: None
    @staticmethod
    def create_from(ir_type:ir.Type | ir.IdentifiedStructType, module:md.Module = None, func = None):
        """
        Create an instance of the type from the llvm IR type.
        This is not inherited and is used to create the correct
        compiler type from an llvmlite.ir Type instance.
        """
        from .types import ArrayType, VoidType, BoolType, I32Type, I8Type, I64Type, F32Type, D64Type
        # check datastructures
        if isinstance(ir_type, ir.ArrayType):
            return ArrayType(CompilerType.create_from(ir_type.element, module, func), ir_type.count)

        ptr_count = ir_type._to_string().count("*")
        
        bool_ = "i1"
        i8 = "i8"
        i32 = "i32"
        i64 = "i64"
        f32 = "float"
        d64 = "double"
        
        chosen_type = I32Type()

        base_type = ir_type._to_string().lstrip("%").replace("\"", "").rstrip("*")

        #print(f"base_type: {base_type}")
        
        if base_type == bool_:
            chosen_type = BoolType()
        elif base_type == i8:
            chosen_type = I8Type()
        elif base_type == i32:
            chosen_type = I32Type()
        elif base_type == i64:
            chosen_type = I64Type()
        elif base_type == f32:
            chosen_type = F32Type()
        elif base_type == d64:
            chosen_type = D64Type()
        else:
            for val in module.structs.values():
                found = False
                for s_key, struct in val.struct_aliases.items():
                    if base_type == s_key:
                        chosen_type = struct.get_type(func)
                        found = True
                        break
                if found: break
                            
        for _ in range(ptr_count):
            chosen_type = chosen_type.cast_ptr()

        #print(f"Original: {ir_type._to_string()}")
        #print(f"Chosen: {chosen_type}")

        return chosen_type

    def render_template(self):
        pass

    @property
    def is_pointer(self):
        return self.value.is_pointer

    @property
    def size(self):
        return self._size
    
    def cast_ptr(self):
        self.value = self.value.as_pointer()
        return self
    def create_ptr(self):
        self_cpy = deepcopy(self)
        self_cpy.value = self_cpy.value.as_pointer()
        return self_cpy
    def __repr__(self) -> str:
        return f"{{{self.value}}}"
    