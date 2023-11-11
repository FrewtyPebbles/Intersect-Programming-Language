from __future__ import annotations
from typing import Dict, List, Union, TYPE_CHECKING
from llvmlite import ir

if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.builder_data import BuilderData
import llvmcompiler.ir_renderers.operations as op
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.ir_renderers.scopes as scps

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
    builder:BuilderData
    def __init__(self, name = "", inside:list[Scope | op.Operation] = [], condition:list[op.Operation] = []) -> None:
        """
        This creates the scope.
        """
        self.name = name
        self.arguments:List[Union[op.Operation, vari.Variable, vari.Value]] = []
        self.inside = inside
        self.builder = None

    def write(self):
        """
        This is used to write the scope to ir
        """
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
        """
        This should be called at the end of the scope.
        """
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

    def write_inner(self, context: ir.IRBuilder):
        last_obj = None
        for inner_obj in self.inside:
            inner_obj.builder = self.builder
            
            if any([isinstance(last_obj, iftype1) for iftype1 in [scps.IfBlock, scps.ElseIfBlock]])\
            and any([isinstance(inner_obj, iftype2) for iftype2 in [scps.ElseIfBlock, scps.ElseBlock]]):
                inner_obj.prev_if = last_obj
            elif any([isinstance(last_obj, iftype1) for iftype1 in [scps.IfBlock, scps.ElseIfBlock, scps.ElseBlock]])\
            and not any([isinstance(inner_obj, iftype2) for iftype2 in [scps.ElseIfBlock, scps.ElseBlock]]):
                last_obj.render()
            
            inner_obj.write()
            last_obj = inner_obj

    def process_arg(self, argument:Union[op.Operation, vari.Variable, vari.Value]):
        processed_arg = None
        if isinstance(argument, op.Operation):
            ret_value = self.write_operation(argument)
            if ret_value != None:
                if isinstance(ret_value, vari.Value):
                    processed_arg = ret_value.get_value()
                elif isinstance(ret_value, vari.Variable):
                    processed_arg = ret_value.variable
        elif isinstance(argument, vari.Variable):
            processed_arg = argument.load()
        elif isinstance(argument, vari.Value):
            processed_arg = argument.get_value()
        
        return processed_arg

    def write_operation(self, operation:op.Operation):
        operation.builder = self.builder
        return operation.write()