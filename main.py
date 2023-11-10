import sys
import time
from llvmcompiler import Function, Value, Module, I32Type, C8Type, ArrayType, I32PointerType, ArrayPointerType, VectorType, BoolType, I8Type
from llvmcompiler.ir_renderers.operations import *

module = Module()

tf = module.create_function("test", {
        "num":I32Type()
    }, I32Type())

builder = tf.builder

# struct test

module.create_struct("Apple", {
    "red": BoolType()
})

builder.write_operation(DefineOperation(["test_struct", Value(module.get_struct("Apple"))]))

# end struct test

# index/for test

ia_str = "This is str 3!\n\0"
builder.write_operation(DefineOperation(["index_array", Value(ArrayType(ArrayType(C8Type(), len(ia_str)), 3))]))
builder.write_operation(AssignOperation([
    IndexOperation([tf.get_variable("index_array"), Value(I32Type(), 0)]),
    Value(ArrayType(C8Type(), len(ia_str)), ia_str)
]))

ia_str = "This is str 2!\n\0"
builder.write_operation(AssignOperation([
    IndexOperation([tf.get_variable("index_array"), Value(I32Type(), 1)]),
    Value(ArrayType(C8Type(), len(ia_str)), ia_str)
]))

ia_str = "This is str 1!\n\0"
builder.write_operation(AssignOperation([
    IndexOperation([tf.get_variable("index_array"), Value(I32Type(), 2)]),
    Value(ArrayType(C8Type(), len(ia_str)), ia_str)
]))

for_loop = builder.create_scope("for")
for_loop.append_condition(DefineOperation(["i", Value(I8Type(), 0)]))
for_loop.append_condition(LessThanOperation([tf.get_variable("i"), Value(I8Type(), 3)]))
for_loop.append_condition(AssignOperation([
    tf.get_variable("i"),
    AddOperation([tf.get_variable("i"), Value(I8Type(), 1)])
]))
for_loop.start_scope()

builder.write_operation(CallOperation(["print", IndexOperation([tf.get_variable("index_array"), tf.get_variable("i")])]))

for_loop.exit_scope()

# end index test

if_scope = builder.create_scope("if")

if_scope.insert_condition(GreaterThanOperation([tf.get_variable("num"), Value(I32Type(), 10)]))
if_scope.start_scope()

gts = "Value is greater than 10\n\0"
builder.write_operation(CallOperation(["print", Value(ArrayType(C8Type(), len(gts)), gts)]))

if_scope.exit_scope()
else_if_scope = if_scope.insert_else_if()
else_if_scope.insert_condition(EqualToOperation([tf.get_variable("num"), Value(I32Type(), 5)]))
else_if_scope.start_scope()

lts = "Value is 5.\n\0"
builder.write_operation(CallOperation(["print", Value(ArrayType(C8Type(), len(lts)), lts)]))

else_if_scope.exit_scope()

else_if_scope2 = else_if_scope.insert_else_if()
else_if_scope2.insert_condition(EqualToOperation([tf.get_variable("num"), Value(I32Type(), 3)]))
else_if_scope2.start_scope()

lts = "Value is 3.\n\0"
builder.write_operation(CallOperation(["print", Value(ArrayType(C8Type(), len(lts)), lts)]))

else_if_scope2.exit_scope()

else_scope = else_if_scope2.insert_else()

else_scope.start_scope()

eqs = "Value is none of the above.\n\0"
builder.write_operation(CallOperation(["print", Value(ArrayType(C8Type(), len(eqs)), eqs)]))

else_scope.exit_scope()

else_scope.render()

closemsg = "Program End msg.\n\0"
builder.write_operation(CallOperation(["print", Value(ArrayType(C8Type(), len(closemsg)), closemsg)]))

builder.write_operation(FunctionReturnOperation([tf.get_variable("num")]))

tf.dbg_print()

#Pseudocode:

"""
fn test(num: i32) -> i32 {
    let heap ret_val:i32 = 10;

    let test_md_array:[[i32 * 3] * 5] = [
        [0,1,2],
        [0,1,2],
        [0,1,2],
        [0,1,2],
        [0,1,2]
    ];

    
    for (let i:i32 = 0; i < 5; i++){
        test_str:str = "%i + (10 * %i) = %i!\n";

        print(test_str, num, i, *ret_val);
        
        *ret_val = *ret_val + 10;
    }

    
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

# print(llvm_module)


tm = llvm.Target.from_default_triple().create_target_machine()

def test(num:int)->int:
    ret_val = 10
    test_str = "{a} + (10 * {b}) = {c}\n"
    for i in range(5):
        sys.stdout.write(test_str.format(a=num, b=i, c=ret_val))
        ret_val = ret_val + num
    return ret_val

# use this https://github.com/numba/llvmlite/issues/181 to figure out how to compile
print("PROGRAM RUNNING:")
with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
    ee.finalize_object()
    fptr = ee.get_function_address("test")
    py_func = CFUNCTYPE(c_int, c_int)(fptr)
    import time
    parameter = 11

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



