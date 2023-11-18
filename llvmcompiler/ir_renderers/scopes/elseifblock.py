from __future__ import annotations
from typing import List, Union, TYPE_CHECKING
import llvmcompiler.ir_renderers.builder_data as bd
import llvmcompiler.ir_renderers.operations as op
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.scopes as scps
from llvmlite import ir


class ElseIfBlock(scps.IfBlock):
    prev_if:scps.IfBlock | scps.ElseIfBlock
    

    def _define_scope_blocks(self):
        self.exit = self.prev_if.exit
        self.builder.cursor.position_at_end(self.prev_if.scope_blocks["start"])
        self.builder.cursor.comment("SCOPE::else_if START")
        self.scope_blocks:dict[str, ir.Block] = {
            # make it so you can for loop without a declaration
            "cond": self.builder.cursor.append_basic_block(),
            "start": self.builder.cursor.append_basic_block()
        }
        self.prev_if.render_br(self.scope_blocks["cond"])
        self.builder.cursor.position_at_end(self.scope_blocks["cond"])
        # Then run define condition when the condition is parsed
        self.processed_arg = None
        self.else_if = False

    def _exit_scope(self):
        # pop the variables
        self.builder.cursor.position_at_end(self.scope_blocks["start"])
        if not self.builder.cursor.block.is_terminated:
            self.builder.cursor.branch(self.prev_if.exit)
        self.builder.cursor.position_at_end(self.prev_if.exit)
        self.scope_end_comment()

    def render(self):
        if not self.else_if:
            self.render_br(self.exit)
            self.builder.cursor.position_at_end(self.exit)

            prev_if = self.prev_if
            while prev_if != None:
                prev_if.render()
                prev_if = self.prev_if

    def scope_end_comment(self):
        self.builder.cursor.comment("SCOPE::else_if END")