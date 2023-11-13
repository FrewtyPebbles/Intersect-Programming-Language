from typing import List, Union
from llvmcompiler.ir_renderers.operations import Operation
from llvmcompiler.ir_renderers.variable import Value, Variable
import llvmcompiler.ir_renderers.scopes as scps
from llvmlite import ir

class IfBlock(scps.Scope):
    def __init__(self, name="", scope: list[scps.Scope | Operation] = [], condition: list[Operation] = []) -> None:
        super().__init__(name, scope, condition)
        self.inside = scope
        self.conditions = condition

    def write(self):
        super().write()
        self.insert_condition(self.conditions[0])
        self.start_scope()
        self.write_inner(self.scope_blocks["start"])
        self.exit_scope()
        
    def _define_scope_blocks(self):
        if_start = self.builder.cursor.comment("SCOPE::if START")
        
        self.scope_blocks:dict[str, ir.Block] = {
            # make it so you can for loop without a declaration
            "start": self.builder.cursor.append_basic_block(),
            "exit": self.builder.cursor.append_basic_block()
        }
        self.exit = self.scope_blocks["exit"]
        self.builder.cursor.position_after(if_start)
        # Then run define condition when the condition is parsed
        self.processed_arg = None
        self.else_if = False
        
    def insert_condition(self, argument:Union[Operation, Variable, Value]):
        self.processed_arg = self.process_arg(argument)
        self.cbr_pos = self.builder.cursor.comment("internal::cbranch_position")
        

    def render_br(self, dest:ir.Block):
        self.builder.cursor.position_after(self.cbr_pos)
        self.builder.cursor.cbranch(self.processed_arg, self.scope_blocks["start"], dest)
        self.builder.cursor.position_at_end(self.exit)

    def start_scope(self):
        """"
        Should be called on "{" token.
        """
        self.builder.cursor.position_at_end(self.scope_blocks["start"])

    def insert_else_if(self):
        """
        For this to work, the syntax tree must maintain a stack of both the previous scope,
        along with a stack of the current scope
        """
        self.else_if = True
        return scps.ElseIfBlock(self.builder, self)

    def insert_else(self):
        """
        For this to work, the syntax tree must maintain a stack of both the previous scope,
        along with a stack of the current scope
        """
        self.else_if = True
        return scps.ElseBlock(self.builder, self)

    def _exit_scope(self):
        # pop the variables
        # self.builder.cursor.position_at_end(self.scope_blocks["start"])

        self.builder.cursor.branch(self.scope_blocks["exit"])
        self.builder.cursor.position_at_end(self.scope_blocks["exit"])
        self.scope_end_comment()

    def render(self):
        """
        Call once if the previous instruction in the previous instruction stack is either an if, else if,
        or an else and the current instruction in the current instruction stack is none of those.
        """
        if not self.else_if:
            self.render_br(self.exit)

    def scope_end_comment(self):
        self.builder.cursor.comment("SCOPE::if END")