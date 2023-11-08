from typing import List, Union
from llvmcompiler.ir_renderers.operations import Operation
from llvmcompiler.ir_renderers.variable import Value, Variable
from .scope import Scope
from llvmlite import ir

class IfBlock(Scope):
    def _define_scope_blocks(self):
        self.builder.cursor.comment("SCOPE::for START")

        self.scope_blocks = {
            # make it so you can for loop without a declaration
            "condition": self.builder.cursor.append_basic_block(),
            "start": self.builder.cursor.append_basic_block(),
            "end": self.builder.cursor.append_basic_block()
        }
        self.builder.cursor.branch(self.scope_blocks["condition"])
        self.builder.cursor.position_at_end(self.scope_blocks["condition"])
        # Then run define condition when the condition is parsed
        self.processed_arg = None
        
    def insert_condition(self, argument:Union[Operation, Variable, Value]):
        if isinstance(argument, Operation):
            value = self.write_operation(argument)
            if value != None:
                self.processed_arg = value.get_value()
        elif isinstance(argument, Variable):
            self.processed_arg = argument.load()
        elif isinstance(argument, Value):
            self.processed_arg = argument.get_value()


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