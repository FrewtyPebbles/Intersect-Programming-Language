from llvmlite import ir
import llvmcompiler.compiler_types.type as ct


class PrecisionType(ct.CompilerType):
    def __init__(self, size:int) -> None:
        self.count = 1
        self._size = size
        if self.size == 32:
            self.value = ir.FloatType()
        elif self.size == 64:
            self.value = ir.DoubleType()
        else:
            print("Error: Not a valid size for a precision type.")

    
class PrecisionPointerType(PrecisionType):
    def __init__(self, size:int) -> None:
        self.count = 1
        self._size = size
        if self.size == 32:
            self.value = ir.FloatType()
        elif self.size == 64:
            self.value = ir.DoubleType()
        else:
            print("Error: Not a valid size for a precision type.")

class F32Type(PrecisionType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 32
        self.value = ir.FloatType()

    

class F32PointerType(PrecisionType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 32
        self.value = ir.FloatType().as_pointer()

class D64Type(PrecisionType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 64
        self.value = ir.DoubleType()

    

class D64PointerType(PrecisionType):
    def __init__(self) -> None:
        self.count = 1
        self._size = 64
        self.value = ir.DoubleType().as_pointer()
    
