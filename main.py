import sys
import time
from llvmcompiler import Function, ScalarType, Operation, OperationType, Value, DataStructureType, DataStructureTypeOptions, Module


module = Module()

tf = module.create_function("test", {
        "num":ScalarType.i32
    }, ScalarType.i32)

builder = tf.builder

builder.write_operation(Operation(OperationType.define, ["ret_val", Value(tf.builder, ScalarType.i32, 10)]))

for_loop = builder.create_scope("for")

for_loop.append_condition(Operation(OperationType.define_heap, ["i", Value(tf.builder, ScalarType.i32, 0)]))
for_loop.append_condition(Operation(OperationType.less_than, [builder.get_variable("i"), Value(tf.builder, ScalarType.i32, 5)]))
for_loop.append_condition(Operation(OperationType.assign, [
        builder.get_variable("i"),
        Operation(OperationType.add, [builder.get_variable("i"), Value(tf.builder, ScalarType.i32, 1)])
    ]))

for_loop.start_scope()

test_str = "Hello, your return value is: %i!\n\0"
for_loop.write_operation(Operation(OperationType.define, [
    "test_str",
    Value(tf.builder, DataStructureType(DataStructureTypeOptions.array, ScalarType.c8, len(test_str)), test_str)
]))

for_loop.write_operation(Operation(OperationType.call, [
    "print", 
    tf.get_variable("test_str"),
    tf.get_variable("ret_val")
]))

for_loop.write_operation(Operation(OperationType.assign, [
    tf.get_variable("ret_val"), 
    Operation(OperationType.add, [
            tf.get_variable("ret_val"), tf.get_variable("num")
        ]
    )
]))

for_loop.exit_scope()


tf.write_operation(Operation(OperationType.function_return, [tf.get_variable("ret_val")]))

tf.dbg_print_module()

#Pseudocode:

"""
fn test(num: i32) -> i32 {
    ret_val: i32 = 7;    

    ret_val = ret_val + 10;

    test_str: str = "Hello, your return value is: %i!\n";

    print(test_str, ret_val);

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

def test(num:int)->int:
    ret_val = 10
    test_str = "Hello, your return value is: {i}!\n"
    for _ in range(5):
        sys.stdout.write(test_str.format(i = ret_val))
        ret_val = ret_val + num
    return ret_val

# use this https://github.com/numba/llvmlite/issues/181 to figure out how to compile

with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
    ee.finalize_object()
    fptr = ee.get_function_address("test")
    py_func = CFUNCTYPE(c_int, c_int)(fptr)
    import time
    parameter = 10

    t0 = time.time()
    ret_ = py_func(parameter)
    t1 = time.time()

    runtime = t1-t0
    print(ret_)
    print(f"compiled runtime:{runtime*1000}ms")


    t0 = time.time()
    ret_ = test(parameter)
    t1 = time.time()

    runtime = t1-t0
    print(ret_)
    print(f"python runtime:{runtime*1000}ms")



