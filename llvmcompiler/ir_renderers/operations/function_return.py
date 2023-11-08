from ..operation import Operation
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari

class FunctionReturnOperation(Operation):
    def _write(self):
        self.builder.cursor.comment("OP::return START")
        self.builder.pop_variables()
        if len(self.arguments) == 0:
            # if type of function is not void then throw an error
            self.builder.cursor.ret_void()
        else:
            # if type of function does not match argument[0].type then throw error
            # self.arguments: 0 = type
            if self.builder.function.return_value.type.is_pointer:
                if self.arguments[0].is_pointer:
                    self.builder.cursor.ret(self.arguments[0])
                else:
                    # throw error because function was expected to return a pointer
                    print(f"Error: Function expected to return a pointer, not {self.arguments[0].type}.")
            else:
                # function does not return a pointer
                if self.arguments[0].is_pointer:
                    self.builder.cursor.ret(self.arguments[0].load())
                else:
                        self.builder.cursor.ret(self.arguments[0].load())
        self.builder.cursor.comment("OP::return END")