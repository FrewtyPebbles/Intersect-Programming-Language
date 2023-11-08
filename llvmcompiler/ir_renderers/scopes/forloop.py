from typing import List, Union
from llvmcompiler.ir_renderers.operations import Operation
from llvmcompiler.ir_renderers.variable import Value, Variable
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
        self.processed_args:List[Union[Operation, Variable, Value]] = []
        
    def append_condition(self, argument:Union[Operation, Variable, Value]):
        processed_arg = None
        if isinstance(argument, Operation):
            ret_value = self.write_operation(argument)
            if ret_value != None:
                if isinstance(ret_value, Value):
                    processed_arg = ret_value.get_value()
                elif isinstance(ret_value, Variable):
                    processed_arg = ret_value.variable
        elif isinstance(argument, Variable):
            processed_arg = argument.load()
        elif isinstance(argument, Value):
            processed_arg = argument.get_value()
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