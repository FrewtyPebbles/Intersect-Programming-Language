import llvmcompiler.ir_renderers.builder_data as bd
from typing import Dict, List
from llvmlite import ir

from llvmcompiler.ir_renderers.operation import Operation
from llvmcompiler.ir_renderers.variable import Variable, Value

class Scope:
    """
    All scope types inherit from this scope.
    Scopes can be used to controll the lifetime of variables ex:
    ```
    { # scope started/created here
        allocate some_var = 5; # Variable allocated to heap here!

        #:
            Do some stuff here!
        :#

        # Variable is deallocated/freed at the end of the scope here automatically!
    }
    ```
    """

    def __init__(self, builder:bd.BuilderData, arguments:List[Operation, Variable, Value] = [], name = "") -> None:
        self.builder = builder
        self.name = name
        self.arguments = arguments
        self._define_scope_blocks()
        self.builder.push_scope(self.scope_blocks)
        self.builder.push_variable_stack()

    def _define_scope_blocks(self):
        """
        This function is where the scope logic should be defined.
        Define all block behaviors here.
        """
        self.scope_blocks = {
            "start": self.builder.cursor.append_basic_block(),
            "end": self.builder.cursor.append_basic_block()
        }
        self.builder.cursor.branch(self.scope_blocks["start"])
        self.builder.cursor.position_at_end(self.scope_blocks["start"])
        
    def exit_scope(self):
        self._exit_scope()
        self.builder.pop_variables()
        self.builder.pop_scope()

    def _exit_scope(self):
        """
        This is where the end of the scope is reached and end of scope behavior is declared.
        Dont forget to pop_variables, pop_heap in scopes with more than one nested variable context.
        ie: for loops where an index is defined
        """
        self.builder.pop_heap()
        self.builder.cursor.branch(self.scope_blocks["end"])
        self.builder.cursor.position_at_end(self.scope_blocks["end"])

    def write_operation(self, operation:Operation):
        operation.builder = self.builder
        return operation.write()