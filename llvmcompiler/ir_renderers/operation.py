from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from typing import List, Tuple, Union
from llvmlite import ir

from llvmcompiler.compiler_types import CompilerType
from llvmcompiler.compiler_types.types.char import C8PointerType
if TYPE_CHECKING:
    from .builder_data import BuilderData
import llvmcompiler.ir_renderers.variable as vari


class Operation:
    """
    All operations inherit from this operation
    """
    def __init__(self, arguments:List[Union[Operation, vari.Variable, CompilerType, vari.Value, any, Tuple[str, vari.Variable]]] = []) -> None:
        self.builder:BuilderData = None
        self.raw_arguments = arguments
        self.arguments = arguments

    def process_arg(self, arg):
        if isinstance(arg, vari.Variable):
            if not arg.heap and not arg.function_argument:
                return arg.load()
            else:
                return arg.variable
        elif isinstance(arg, vari.Value):
            return arg.get_value()
        else:
            return arg
        
    def process_lhs_rhs_args(self):
        #process arg1
        arg1 = self.process_arg(self.arguments[0])
        
        #process arg2
        arg2 = self.process_arg(self.arguments[1])

        return arg1, arg2

    def write_arguments(self):
        """
        This function processes the arguments of the operation and runs any operation arguments.
        """
        # process the arguments and run any operation arguments
        for r_a_n, raw_arg in enumerate(self.raw_arguments):
            if isinstance(raw_arg, Operation):
                value = self.builder.scope.write_operation(raw_arg)
                self.arguments[r_a_n] = value
            else:
                self.arguments[r_a_n] = raw_arg
        print(self)

    def _write(self) -> vari.Value | vari.Variable:
        """
        This should be overridden to in inheriting class.
        This function is what is called to write the ir for the operation
        """
        

    def write(self):
        self.write_arguments()
        return self._write()

    def __repr__(self) -> str:
        return f"({self.__class__.__name__}:[arguments:{self.arguments}])"

        

        

def dbg_llvm_print(builder:BuilderData, var):
    srcstr = "%i\n\00"
    string = builder.alloca(ir.ArrayType(ir.IntType(8), len(srcstr)))
    builder.cursor.store(ir.Constant(ir.ArrayType(ir.IntType(8), len(srcstr)), bytearray(srcstr.encode("utf8"))), string)
    builder.cursor.call(builder.functions["print"], [builder.cursor.bitcast(string, C8PointerType().value), var])