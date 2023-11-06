import time
from llvmcompiler import Function, ScalarType, Operation, OperationType, Value, DataStructureType, DataStructureTypeOptions
from llvmlite import ir

module = ir.Module()

tf = Function(module,"test", {
        "num1":ScalarType.i32,
        "num2":ScalarType.i32
    }, ScalarType.i32)

tf.write_operation(Operation(OperationType.define, ["ret_val", Value(tf.builder, ScalarType.i32, 10)]))
tf.write_operation(Operation(OperationType.assign, [
    tf.get_variable("ret_val"), 
    Operation(OperationType.add, [
            tf.get_variable("ret_val"), Value(tf.builder, ScalarType.i32, 7)
        ]
    )
]))

test_str = "Hello, your return value is: %i!\n\0"
tf.write_operation(Operation(OperationType.define_heap, ["test_str", Value(tf.builder, DataStructureType(DataStructureTypeOptions.array, ScalarType.c8, len(test_str)), test_str)]))

tf.write_operation(Operation(OperationType.call, [
    "print", 
    tf.get_variable("test_str"),
    Operation(OperationType.dereference, [tf.get_variable("ret_val")])
]))

tf.write_operation(Operation(OperationType.function_return, [tf.get_variable("ret_val")]))

tf.dbg_print_module()

import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, POINTER


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()
llvm_module = llvm.parse_assembly(str(module))
tm = llvm.Target.from_default_triple().create_target_machine()

with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
    ee.finalize_object()
    fptr = ee.get_function_address("test")
    py_func = CFUNCTYPE(c_int, c_int, c_int)(fptr)
    ret_ = py_func(1, 2)

    print(ret_)