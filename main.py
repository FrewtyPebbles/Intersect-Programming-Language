import time
from llvmcompiler import Function, ScalarType, Operation, OperationType, Value, DataStructureType, DataStructureTypeOptions, Module


module = Module()

tf = module.create_function("test", {
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
tf.write_operation(Operation(OperationType.define, [
    "test_str",
    Value(tf.builder, DataStructureType(DataStructureTypeOptions.array, ScalarType.c8, len(test_str)), test_str)
]))

tf.write_operation(Operation(OperationType.call, [
    "print", 
    tf.get_variable("test_str"),
    tf.get_variable("ret_val")
]))

tf.write_operation(Operation(OperationType.function_return, [tf.get_variable("ret_val")]))

tf.dbg_print_module()

#Pseudocode:

"""
fn test(num1: i32, num2: i32) -> i32 {
    
    return ret_val;
}

"""

import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, POINTER


llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()
llvm_module = llvm.parse_assembly(str(module))

# optimizer
pm = llvm.create_module_pass_manager()
pmb = llvm.create_pass_manager_builder()
pmb.opt_level = 3  # -O3
pmb.populate(pm)

# run optimizer

# optimize
pm.run(llvm_module)

print(llvm_module)


tm = llvm.Target.from_default_triple().create_target_machine()

def test(num1:int, num2:int)->int:
    ret_val = 10
    ret_val = ret_val + 7
    test_str = "Hello, your return value is: {i}!\n"
    print(test_str.format(i = ret_val))
    return ret_val

# use this https://github.com/numba/llvmlite/issues/181 to figure out how to compile

with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
    ee.finalize_object()
    fptr = ee.get_function_address("test")
    py_func = CFUNCTYPE(c_int, c_int, c_int)(fptr)
    import time

    t0 = time.time()
    ret_ = py_func(1, 2)
    t1 = time.time()

    runtime = t1-t0
    print(f"compiled runtime:{runtime*1000}ms")
    print(ret_)


    t0 = time.time()
    ret_ = test(1, 2)
    t1 = time.time()

    runtime = t1-t0
    print(f"python runtime:{runtime*1000}ms")
    print(ret_)



