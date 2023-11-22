from llvmlite import ir
from copy import deepcopy, copy

class CompilerType:
    """
    This class is inherited by all type classes.
    """
    _size:int
    value:ir.Type
    parent: None
    module: None
    @staticmethod
    def create_from(ir_type:ir.Type):
        """
        Create an instance of the type from the llvm IR type.
        This is not inherited and is used to create the correct
        compiler type from an llvmlite.ir Type instance.
        """
        from .types import ArrayType, VoidType, BoolType, I32Type, I8Type, I64Type, F32Type, D64Type
        # check datastructures
        if isinstance(ir_type, ir.ArrayType):
            return ArrayType(CompilerType.create_from(ir_type.element), ir_type.count)

        # check Scalars
        if ir_type == ir.VoidType():
            return VoidType()
        elif ir_type == ir.IntType(1):
            return BoolType()
        elif ir_type == ir.IntType(8):
            return I8Type()
        elif ir_type == ir.IntType(32):
            return I32Type()
        elif ir_type == ir.IntType(64):
            return I64Type()
        elif ir_type == ir.FloatType():
            return F32Type()
        elif ir_type == ir.DoubleType():
            return D64Type()
        # pointer scalars
        elif ir_type == ir.IntType(1).as_pointer():
            return BoolType().cast_ptr()
        elif ir_type == ir.IntType(8).as_pointer():
            return I8Type().cast_ptr()
        elif ir_type == ir.IntType(32).as_pointer():
            return I32Type().cast_ptr()
        elif ir_type == ir.IntType(64).as_pointer():
            return I64Type().cast_ptr()
        elif ir_type == ir.FloatType().as_pointer():
            return F32Type().cast_ptr()
        elif ir_type == ir.DoubleType().as_pointer():
            return D64Type().cast_ptr()

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
    