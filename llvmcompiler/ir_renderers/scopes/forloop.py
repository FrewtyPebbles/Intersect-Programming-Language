from __future__ import annotations
from typing import List, Union
import llvmcompiler.ir_renderers.operations as op
import llvmcompiler.ir_renderers.variable as vari
from .scope import Scope

class ForLoop(Scope):
    def _define_scope_blocks(self):
        self.builder.cursor.comment("SCOPE::for START")

        self.scope_blocks = {
            # make it so you can for loop without a declaration
            "declaration": self.builder.cursor.append_basic_block(),
            "condition": self.builder.cursor.append_basic_block(),
            "increment": self.builder.cursor.append_basic_block(),
            "start": self.builder.cursor.append_basic_block(),
            "end": self.builder.cursor.append_basic_block()
        }
        self.builder.cursor.branch(self.scope_blocks["declaration"])
        self.builder.cursor.position_at_end(self.scope_blocks["declaration"])
        # Then run define condition when the condition is parsed
        self.processed_args:List[Union[op.Operation, vari.Variable, vari.Value]] = []
        
    def append_condition(self, argument:Union[op.Operation, vari.Variable, vari.Value]):
        processed_arg = self.process_arg(argument)
        self.processed_args.append(processed_arg)
        if len(self.processed_args) == 1:
            self.builder.cursor.branch(self.scope_blocks["condition"])
            self.builder.cursor.position_at_end(self.scope_blocks["condition"])
        if len(self.processed_args) == 2:
            self.builder.cursor.cbranch(self.processed_args[1], self.scope_blocks["start"], self.scope_blocks["end"])
            self.builder.cursor.position_at_end(self.scope_blocks["increment"])
        if len(self.processed_args) == 3:
            self.builder.cursor.branch(self.scope_blocks["condition"])

    def start_scope(self):
        # define the condition
        # branch to the start of the loop
        

        self.builder.push_variable_stack()
        self.builder.cursor.position_at_end(self.scope_blocks["start"])

    def _exit_scope(self):
        # pop the variables
        self.builder.pop_variables()
        self.builder.cursor.branch(self.scope_blocks["increment"])
        self.builder.cursor.position_at_end(self.scope_blocks["end"])
        self.builder.cursor.comment("SCOPE::for END")