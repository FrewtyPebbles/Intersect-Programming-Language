from __future__ import annotations
from typing import List, Union, TYPE_CHECKING
from .scope import Scope

if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.operations as op
    import llvmcompiler.ir_renderers.variable as vari


class WhileLoop(Scope):
    def __init__(self, name="", scope: list[Scope | op.Operation] = [], condition: list[op.Operation] = []) -> None:
        super().__init__(name, scope, condition)
        self.inside = scope
        self.conditions = condition

    def write(self):
        super().write()
        self.builder.push_scope(self.scope_blocks["end"])
        for condition in self.conditions:
            self.append_condition(condition)
        self.start_scope()
        self.write_inner()
        self.exit_scope()


    def _define_scope_blocks(self):
        self.builder.cursor.comment("SCOPE::while START")
        self.scope_blocks = {
            # make it so you can for loop without a declaration
            "condition": self.builder.cursor.append_basic_block(),
            "start": self.builder.cursor.append_basic_block(),
            "end": self.builder.cursor.append_basic_block()
        }
        self.builder.cursor.branch(self.scope_blocks["condition"])
        self.builder.cursor.position_at_end(self.scope_blocks["condition"])
        # Then run define condition when the condition is parsed
        self.processed_args:List[Union[op.Operation, vari.Variable, vari.Value]] = []
        
    def append_condition(self, argument:Union[op.Operation, vari.Variable, vari.Value]):
        processed_arg = self.process_arg(argument)
        self.processed_args.append(processed_arg)
        self.builder.cursor.cbranch(self.processed_args[0], self.scope_blocks["start"], self.scope_blocks["end"])

    def start_scope(self):
        # define the condition
        # branch to the start of the loop
        
        self.builder.push_variable_stack()
        self.builder.cursor.position_at_end(self.scope_blocks["start"])

    def _exit_scope(self):
        # pop the variables
        print(self.builder.memory_top.variables_stack)
        self.builder.pop_variables()
        if not self.builder.cursor.block.is_terminated:
            self.builder.cursor.branch(self.scope_blocks["condition"])
        self.builder.cursor.position_at_end(self.scope_blocks["end"])
        self.builder.cursor.comment("SCOPE::while END")
        self.builder.pop_scope()