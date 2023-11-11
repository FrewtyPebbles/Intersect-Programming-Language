import sys
import time
from llvmcompiler import Function, Value, Module, I32Type, C8Type, ArrayType, I32PointerType,\
     ArrayPointerType, VectorType, BoolType, I8Type, ForLoop, VoidType, IfBlock, ElseBlock, ElseIfBlock
from llvmcompiler.ir_renderers.operations import *


module = Module("testmod.pop",scope=[
    Function("print_something", {}, VoidType(), scope=[

        CallOperation(["print", [Value(ArrayType(C8Type(), len("less than 5\n\0")), "less than 5\n\0")]]),
        
        FunctionReturnOperation([])
    ]),

    Function("test", {"num":I32Type()}, I32Type(), scope=[
        IfBlock(condition=[LessThanOperation(["num", Value(I32Type(), 5)])], scope=[
            
            ForLoop(condition=[
                DefineOperation(["i", Value(I32Type(), 0)]),
                LessThanOperation(["i", "num"]),
                AssignOperation(["i", AddOperation(["i", Value(I32Type(), 1)])])
            ],scope=[

                CallOperation(["print_something", []])

            ]),
            
        ]),
        ElseIfBlock(condition=[
            GreaterThanOperation(["num", Value(I32Type(), 6)])
        ],scope=[
            CallOperation(["print", [Value(ArrayType(C8Type(), len("greater than 6\n\0")), "greater than 6\n\0")]]),
        ]),
        ElseBlock(scope=[
            CallOperation(["print", [Value(ArrayType(C8Type(), len("else\n\0")), "else\n\0")]]),
        ]),
        
        CallOperation(["print", [Value(ArrayType(C8Type(), len("after\n\0")), "after\n\0")]]),

        FunctionReturnOperation(["num"])

    ])
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



