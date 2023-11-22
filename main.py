import sys
import time
from llvmcompiler import Function, Value, Module, I32Type, C8Type, ArrayType, I32PointerType,\
     ArrayPointerType, VectorType, BoolType, I8Type, ForLoop, VoidType, IfBlock, ElseBlock,\
    ElseIfBlock, FunctionDefinition, Template, TemplatePointer, StructDefinition, StructType, HeapValue,\
    StructPointerType, LookupLabel, C8PointerType, WhileLoop, I8PointerType
from llvmcompiler.ir_renderers.operations import *




module = Module("testmod.pop",scope=[
    StructDefinition("Vector", {
        "data":TemplatePointer("ItemType"),
        "length":I64Type()
    }, [
        FunctionDefinition("init", {
            "self":StructPointerType("Vector", [Template("ItemType")])
        }, VoidType(),scope=[
            AssignOperation([
                IndexOperation(["self", LookupLabel("data")]),
                CastOperation([
                    CallOperation("libc_malloc", [TypeSizeOperation([Template("ItemType")])]), 
                    TemplatePointer("ItemType")
                ])
            ]),
            FunctionReturnOperation()
        ]),
        FunctionDefinition("del", {
            "self":StructPointerType("Vector", [Template("ItemType")]),
        }, VoidType(),scope=[
            CallOperation("libc_free", [CastOperation([
                IndexOperation(["self", LookupLabel("data")]),
                I8PointerType()
            ])]),
            FunctionReturnOperation()
        ])
    ], ["ItemType"]),
    FunctionDefinition("test", {"num":I32Type()}, I32Type(), scope=[
        DefineOperation(["vec", Value(StructType("Vector", [I32Type()]))]),
        CallOperation(IndexOperation(["vec", LookupLabel("init")]), []),
        CallOperation(IndexOperation(["vec", LookupLabel("del")]), []),
        FunctionReturnOperation([Value(I32Type(), 1)])
    ], extern=True)
])


module.write()

module.dbg_print()


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


# use this https://github.com/numba/llvmlite/issues/181 to figure out how to compile
print("PROGRAM RUNNING:")
with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
    ee.finalize_object()
    fptr = ee.get_function_address("test")
    py_func = CFUNCTYPE(c_int, c_int)(fptr)
    import time
    parameter = int(input())

    t0 = time.time()
    ret_ = py_func(parameter)
    t1 = time.time()

    runtime = t1-t0
    print(ret_)
    print(f"compiled runtime:{runtime*1000}ms")




