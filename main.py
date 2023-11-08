import sys
import time
from llvmcompiler import Function, Value, Module, I32Type, C8Type, ArrayType, I32PointerType
from llvmcompiler.ir_renderers.operations import *

module = Module()

tf = module.create_function("test", {
        "num":I32Type()
    }, I32Type())

builder = tf.builder

builder.write_operation(DefineOperation(["ret_val", Value(tf.builder, I32Type(), 10)]))
builder.write_operation(DefineOperation(["test_md_array", Value(tf.builder, ArrayType(ArrayType(I32Type(), 3), 5), [[0,1,2],[0,1,2],[0,1,2],[0,1,2],[0,1,2]])]))

for_loop = builder.create_scope("for")

for_loop.append_condition(DefineOperation(["i", Value(tf.builder, I32Type(), 0)]))
for_loop.append_condition(LessThanOperation([builder.get_variable("i"), Value(tf.builder, I32Type(), 5)]))
for_loop.append_condition(AssignOperation([
        builder.get_variable("i"),
        AddOperation([builder.get_variable("i"), Value(tf.builder, I32Type(), 1)])
    ]))

for_loop.start_scope()

test_str = "%i + %i = %i\n\0"
for_loop.write_operation(DefineOperation([
    "test_str",
    Value(tf.builder, ArrayType(C8Type(), len(test_str)), test_str)
]))


for_loop.write_operation(CallOperation([
    "print", 
    tf.get_variable("test_str"),
    tf.get_variable("ret_val"),
    tf.get_variable("num"),
    tf.get_variable("ret_val")
]))

for_loop.write_operation(AssignOperation([
    tf.get_variable("ret_val"), 
    AddOperation([
            tf.get_variable("ret_val"), tf.get_variable("num")
        ]
    )
]))


for_loop.exit_scope()


tf.write_operation(FunctionReturnOperation([tf.get_variable("ret_val")]))


#Pseudocode:

"""
fn test(num: i32) -> i32 {
    ret_val: i32 = 7;    

    {}
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



