from __future__ import annotations
import sys
from llvmlite import ir
from copy import deepcopy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import llvmcompiler.modules.module as md
IS_64BIT = sys.maxsize > 2**32

class CompilerType:
    """
    This class is inherited by all type classes.
    """

    
    _size:int
    value:ir.Type
    parent: None
    module: None
    ptr_count:int
    name: str
    "This is the name used in the original source file."
    @staticmethod
    def create_from(ir_type:ir.Type | ir.IdentifiedStructType, module:md.Module = None, func = None):
        """
         - IMPORTANT: DOES NOT WORK WITH TEMPLATED TYPES

        Create an instance of the type from the llvm IR type.
        This is not inherited and is used to create the correct
        compiler type from an llvmlite.ir Type instance.
        """
        from .types import ArrayType, VoidType, BoolType, I32Type, I8Type, I64Type, F32Type, D64Type
        
        #raise RuntimeError("DEPRECIATING")

        ptr_count = ir_type._to_string().count("*")
        
        bool_ = "i1"
        i8 = "i8"
        i32 = "i32"
        i64 = "i64"
        f32 = "float"
        d64 = "double"
        
        chosen_type = I32Type()

        base_type = ir_type._to_string().lstrip("%").replace("\"", "").rstrip("*")
        # get pointee
        type_pointee = ir_type
        while hasattr(type_pointee, "pointee"):
            type_pointee = type_pointee.pointee
        # check datastructures
        if all([s in base_type for s in "[x]"]):
            #print(type_pointee.element)
            chosen_type = ArrayType(CompilerType.create_from(type_pointee.element, module, func), type_pointee.count)
        elif base_type == bool_:
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
                    s_key = s_key.replace(f'\\22', '')
                    #print(f"GET TYPE {s_key} == {base_type}")
                    if base_type == s_key:
                        chosen_type = struct.get_type(func)
                        found = True
                        break
                if found: break
                            
        chosen_type.ptr_count = ptr_count

        
        #print(f"CTYPE {chosen_type}")
        return chosen_type

    def render_template(self):
        pass

    @property
    def is_pointer(self):
        return self.value.is_pointer

    @property
    def size(self):
        if self.ptr_count > 0:
            if IS_64BIT:
                return self._size + 64
            else:
                return self._size + 32
        return self._size
    
    def cast_ptr(self):
        self.value = self.value.as_pointer()
        return self
    
    def deref_ptr(self):
        self.value = self.value.pointee
        if self.ptr_count > 0:
            self.ptr_count -= 1
        return self
    
    def create_ptr(self):
        self_cpy = deepcopy(self)
        self_cpy.value = self_cpy.value.as_pointer()
        return self_cpy

    def create_deref(self):
        self_cpy = deepcopy(self)
        if self_cpy.ptr_count > 0:
            self_cpy.ptr_count -= 1
        if hasattr(self_cpy.value, "pointee"):
            self_cpy.value = self_cpy.value.pointee
        return self_cpy

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"parent", "module", "builder", "value",
                "_value", "_count", "count", "_size", "size", "name"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result

    def __repr__(self) -> str:
        if hasattr(self, "ptr_count"):
            return f"{'$'*self.ptr_count}{self.name}"
        return self.name
    