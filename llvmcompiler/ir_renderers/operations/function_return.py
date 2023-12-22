from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class FunctionReturnOperation(Operation):
    def __init__(self, arguments: list = None) -> None:
        super().__init__(arguments)
        self.struct_operator = False
    def _write(self):
        self.builder.cursor.comment("OP::return START")
        self.arguments = self.get_variables()
        # self.builder.pop_variables()
        if len(self.arguments) == 0:
            # if type of function is not void then throw an error
            self.builder.cursor.ret_void()
        else:
            # if type of function does not match argument[0].type then throw error
            # self.arguments: 0 = type
            arg = self.process_arg(self.arguments[0])
            self.builder.cursor.ret(arg)
        self.builder.cursor.comment("OP::return END")
        