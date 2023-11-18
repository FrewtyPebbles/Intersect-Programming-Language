import sys
import time
from llvmcompiler import Function, Value, Module, I32Type, C8Type, ArrayType, I32PointerType,\
     ArrayPointerType, VectorType, BoolType, I8Type, ForLoop, VoidType, IfBlock, ElseBlock,\
    ElseIfBlock, FunctionDefinition, Template, StructDefinition, StructType, HeapValue,\
    StructPointerType, LookupLabel, C8PointerType
from llvmcompiler.ir_renderers.operations import *




module = Module("testmod.pop",scope=[
    StructDefinition("Vector",{
        "data":ArrayType(Template("ArrayType"), 3),
        "length":I32Type()
    },[
        FunctionDefinition("new", {"self":StructPointerType("Vector", [Template("ArrayType")]), "arg":I32Type()}, VoidType(), scope=[
            CallOperation("libc_printf", [CastOperation([Value(ArrayType(C8Type(), len("index 1 value: %i\n\0")), "index 1 value: %i\n\0"), C8PointerType()]),
                DereferenceOperation([IndexOperation(["self", LookupLabel("data"), Value(I32Type(), 1)])])
            ]),
            AssignOperation([IndexOperation(["self", LookupLabel("data"), Value(I32Type(), 1)]), "arg"]),
            FunctionReturnOperation([])
        ])
    ],["ArrayType"]),
    
    FunctionDefinition("print_something", {}, Template("A"), scope=[
        DefineOperation(["number", Value(Template("A"), 5)]),
        DefineOperation(["test_struct",Value(StructType("Vector", [I32Type()]))]),

        CallOperation("libc_printf", [
            CastOperation([Value(ArrayType(Template("B"), len("Heres a number: %i\n\0")), "Heres a number: %i\n\0"), C8PointerType()]),
            "number"
        ]),
        
        FunctionReturnOperation(["number"])
    ], template_args=["A","B"]),

    FunctionDefinition("print_something_inbetween", {}, Template("B"), scope=[
        FunctionReturnOperation([
            
            CallOperation("print_something", [], [Template("B"), Template("A")])
            
        ])

    ], template_args=["A", "B"]),

    FunctionDefinition("test", {"num":I32Type()}, I32Type(), scope=[
        DefineOperation(["testMD1",
            ConstructListOperation(StructPointerType("Vector", [I32Type()]), [
                ConstructStructOperation("Vector", {
                    "data": ConstructListOperation(I32Type(), [
                        Value(I32Type(), 1),
                        Value(I32Type(), 2),
                        Value(I32Type(), 3)
                    ]),
                    "length": Value(I32Type(), 3)
                }, [I32Type()], True)
            ], False)
        ]),

        #
        DefineOperation(["testVEC",
            ConstructStructOperation("Vector", {
                "data": ConstructListOperation(I32Type(), [
                    Value(I32Type(), 1),
                    Value(I32Type(), 2),
                    Value(I32Type(), 3)
                ]),
                "length": Value(I32Type(), 3)
            }, [I32Type()], True)
        ]),
        #
        
        CallOperation(IndexOperation(["testVEC", LookupLabel("new")]), ["num"]),
        CallOperation(IndexOperation(["testVEC", LookupLabel("new")]), ["num"]),

        IfBlock(condition=[LessThanOperation(["num", Value(I32Type(), 100000)])], scope=[
            
            ForLoop(condition=[
                DefineHeapOperation(["i", Value(I32Type(), 0)]),
                LessThanOperation([DereferenceOperation(["i"]), "num"]),
                AssignOperation(["i", AddOperation([DereferenceOperation(["i"]), Value(I32Type(), 1)])])
            ],scope=[

                CallOperation("print_something_inbetween", [], [C8Type(), I32Type()])

            ]),
            
        ]),
        ElseIfBlock(condition=[
            GreaterThanOperation(["num", Value(I32Type(), 100000)])
        ],scope=[

            CallOperation("libc_printf", [
                CastOperation([Value(ArrayType(C8Type(), len("greater than 300\n\0")), "greater than 300\n\0"), C8PointerType()])
            ]),
        
        ]),
        ElseBlock(scope=[
        
            CallOperation("libc_printf", [
                CastOperation([Value(ArrayType(C8Type(), len("else\n\0")), "else\n\0"), C8PointerType()])
            ]),
        
        ]),
        
        CallOperation("libc_printf", [
            CastOperation([Value(ArrayType(C8Type(), len("after\n\0")), "after\n\0"), C8PointerType()])
        ]),

        FunctionReturnOperation(["num"])
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




