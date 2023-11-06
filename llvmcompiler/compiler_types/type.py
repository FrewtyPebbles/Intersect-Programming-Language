from __future__ import annotations
from typing import Union, Dict
from llvmlite import ir
from enum import Enum


class ScalarType(Enum):
    i32 = ir.IntType(32)
    i64 = ir.IntType(64)
    i8 = ir.IntType(8)
    bool = ir.IntType(1)
    c8 = ir.IntType(8)
    d64 = ir.DoubleType()
    f32 = ir.FloatType()
    void = ir.VoidType()
    i32_ptr = ir.IntType(32).as_pointer()
    i64_ptr = ir.IntType(64).as_pointer()
    c8_ptr = ir.IntType(8).as_pointer()
    i8_ptr = ir.IntType(8).as_pointer()
    bool_ptr = ir.IntType(1).as_pointer()
    d64_ptr = ir.DoubleType().as_pointer()
    f32_ptr = ir.FloatType().as_pointer()

    def __init__(self, *args) -> None:
        super().__init__()
        self._size = 0
        if self.name in {"i32", "i32_ptr", "f32", "f32_ptr"}:
            self._size = 32
        elif self.name in {"i64", "i64_ptr", "d64", "d64_ptr"}:
            self._size = 64
        elif self.name in {"c8", "i8", "c8_ptr", "i8_ptr"}:
            self._size = 8
        elif self.name in {"bool", "bool_ptr"}:
            self._size = 1


    def cast_ptr(self):
        if "ptr" in self.name:
            return self
        else:
            return ScalarType[f"{self.name}_ptr"]

    @property
    def is_pointer(self):
        return self.value.is_pointer

    @property
    def size(self):
        return self._size


class DataStructureTypeOptions(Enum):
    array = 0
    vector = 1
    struct = 2
    array_ptr = 3
    vector_ptr = 4
    struct_ptr = 5

class DataStructureType:
    def __init__(self, datastructure_type:DataStructureTypeOptions, items_type:AnyType, count:int = 0) -> None:
        #set value
        self.count = count
        
        self._size = self.count * items_type.size

        self.type = items_type
        self.ds_type = datastructure_type
        if datastructure_type == DataStructureTypeOptions.array:
            self.value = ir.ArrayType(items_type.value, self.count)
        elif datastructure_type == DataStructureTypeOptions.vector:
            self.value = ir.VectorType(items_type.value, self.count)
        elif datastructure_type == DataStructureTypeOptions.struct:
            self.value = ir.BaseStructType()
        elif datastructure_type == DataStructureTypeOptions.array_ptr:
            self.value = ir.ArrayType(items_type.value, self.count).as_pointer()
        elif datastructure_type == DataStructureTypeOptions.vector_ptr:
            self.value = ir.VectorType(items_type.value, self.count).as_pointer()
        elif datastructure_type == DataStructureTypeOptions.struct_ptr:
            self.value = ir.BaseStructType().as_pointer()
    @staticmethod
    def create_from(ir_type:ir.Type):
        ds_type, items_type, count = None
        count = ir_type.count
        if isinstance(ir_type, ir.ArrayType):
            ds_type = DataStructureTypeOptions.array
        elif isinstance(ir_type, ir.VectorType):
            ds_type = DataStructureTypeOptions.vector
        elif isinstance(ir_type, ir.BaseStructType):
            ds_type = DataStructureTypeOptions.struct
        # Pointer types may cause problems later, keep these in the back of your mind
        elif isinstance(ir_type, ir.PointerType):
            ds_type = DataStructureTypeOptions.array_ptr
        elif isinstance(ir_type, ir.PointerType):
            ds_type = DataStructureTypeOptions.vector_ptr
        elif isinstance(ir_type, ir.PointerType):
            ds_type = DataStructureTypeOptions.struct_ptr
        items_type = ir_type.element
        dst = DataStructureType(ds_type, items_type, count)

    def cast_ptr(self):
        if self.ds_type == DataStructureTypeOptions.array:
            return DataStructureType(DataStructureTypeOptions.array_ptr, self.type, self.count)
        elif self.ds_type == DataStructureTypeOptions.vector:
            return DataStructureType(DataStructureTypeOptions.array_ptr, self.type, self.count)
        elif self.ds_type == DataStructureTypeOptions.struct:
            return DataStructureType(DataStructureTypeOptions.array_ptr, self.type, self.count)
        else:
            return self

    @property
    def is_pointer(self):
        return self.value.is_pointer
    
    @property
    def size(self):
        return self._size
    

AnyType = Union[ScalarType, DataStructureType]

def is_ptr(_type) -> bool:
    return (_type in\
        {ScalarType.c8_ptr, ScalarType.d64_ptr, ScalarType.f32_ptr, ScalarType.i32_ptr, ScalarType.i64_ptr}\
        if (isinstance(_type, ScalarType)) else isinstance(_type, DataStructureType))

def ir_is_ptr(_type) -> bool:
    return issubclass(type(_type), ir.PointerType)

def create_type(ir_type:ir.Type):
    try:
        return ScalarType(ir_type)
    except:
        DataStructureType.create_from(ir_type)