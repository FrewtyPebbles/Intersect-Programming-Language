from __future__ import annotations
from typing import Union, Dict
from llvmlite import ir
from enum import Enum


class ScalarType(Enum):
    i32 = ir.IntType(32)
    i64 = ir.IntType(64)
    c8 = ir.IntType(8)
    d64 = ir.DoubleType()
    f32 = ir.FloatType()
    void = ir.VoidType()
    i32_ptr = ir.IntType(32).as_pointer()
    i64_ptr = ir.IntType(64).as_pointer()
    c8_ptr = ir.IntType(8).as_pointer()
    d64_ptr = ir.DoubleType().as_pointer()
    f32_ptr = ir.FloatType().as_pointer()

class DataStructureTypeOptions(Enum):
    array = 0
    vector = 1
    struct = 2

class DataStructureType:
    def __init__(self, datastructure_type:DataStructureTypeOptions, items_type:AnyType, count:int = 0) -> None:
        #set value
        if items_type == ScalarType.c8:
                # add to count for null terminator if it is a string
                count = count + 1
        
        self.type = items_type
        if datastructure_type == DataStructureTypeOptions.array:
            self.value = ir.ArrayType(items_type.value, count)
        elif datastructure_type == DataStructureTypeOptions.vector:
            self.value = ir.VectorType(items_type.value, count)
        elif datastructure_type == DataStructureTypeOptions.struct:
            self.value = ir.BaseStructType()

AnyType = Union[ScalarType, DataStructureType]

def is_ptr(_type) -> bool:
    return (_type in\
        {ScalarType.c8_ptr, ScalarType.d64_ptr, ScalarType.f32_ptr, ScalarType.i32_ptr, ScalarType.i64_ptr}\
        if (isinstance(_type, ScalarType)) else isinstance(_type, DataStructureType))

def ir_is_ptr(_type) -> bool:
    print(type(_type))
    return issubclass(type(_type), ir.PointerType)