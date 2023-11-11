from __future__ import annotations
from typing import Dict, List, Union, TYPE_CHECKING
from llvmlite import ir
import llvmcompiler.ir_renderers.builder_data as bd
from llvmcompiler.ir_renderers.operations import Operation
from llvmcompiler.ir_renderers.scopes.forloop import ForLoop
import llvmcompiler.ir_renderers.scopes as scps

import llvmcompiler.ir_renderers.variable as var

if TYPE_CHECKING:
    from llvmcompiler.modules.module import Module
import llvmcompiler.compiler_types as ct




class Function:
    module:Module
    def __init__(self, name:str, arguments:Dict[str, ct.CompilerType],
            return_type:ct.CompilerType, variable_arguments:bool = False, template_args:list[ct.Template] = [],
            scope:list[scps.Scope | Operation] = []) -> None:
        self.name = name
        self.arguments = arguments
        self.return_type = return_type
        self.variable_arguments = variable_arguments
        # this is all variables within the function scope
        self.variables:Dict[str, var.Variable] = [{}]
        self.scope = scope
        self.template_args = template_args
        self.template_types:list[ct.CompilerType] = []
        self.is_template_function = len(template_args) > 0
        self.struct:ct.Struct = None
        self.module = None
        self.function:dict[str, ir.Function] = {
            #dict containing function and mangled aliases
        }

    def get_template_index(self, name:str):
        return self.template_args.index(name)

    def write(self, template_types:list[ct.CompilerType] = [], initial_render = False):
        self.template_types = template_types
        mangled_name = self.get_mangled_name(template_types)
        if mangled_name in self.module.existing_mangled_names:
            return mangled_name

        if self.is_template_function and len(template_types) < len(self.template_args):
            if not initial_render:
                print("Error: Not enough template arguments were provided in function call!")
                return
        # ^skips if uses templates but not enough were provided

        func_args, func_ret = self.get_function_template_signature()

        

        self.function_type = ir.FunctionType(func_ret.value, [stype.value for stype in func_args.values()], var_arg=self.variable_arguments)
        
        self.function[mangled_name] = ir.Function(self.module.module, self.function_type, mangled_name)
        # name the function arguments
        for arg_num, arg in enumerate(func_args.keys()):
            self.function[mangled_name].args[arg_num].name = arg
        
        # get a ir cursor for writing ir to different things in the function
        self.entry = self.function[mangled_name].append_basic_block("entry")
        self.builder = bd.BuilderData(self, ir.IRBuilder(self.entry), self.variables)
        self.builder.declare_arguments()
        # This cursor needs to be passed to any ir building classes that are used
        # within this function.

        self.get_variable = self.builder.get_variable

        # write the scope

        self.write_scope()
        
        # end write the scope



        self.module.existing_mangled_names.append(mangled_name)


        return mangled_name

    def write_scope(self):
        last_scope_line = None
        for scope_line in self.scope:
            scope_line.builder = self.builder

            if any([isinstance(last_scope_line, iftype1) for iftype1 in [scps.IfBlock, scps.ElseIfBlock]])\
            and any([isinstance(scope_line, iftype2) for iftype2 in [scps.ElseIfBlock, scps.ElseBlock]]):
                scope_line.prev_if = last_scope_line
            elif any([isinstance(last_scope_line, iftype1) for iftype1 in [scps.IfBlock, scps.ElseIfBlock, scps.ElseBlock]])\
            and not any([isinstance(scope_line, iftype2) for iftype2 in [scps.ElseIfBlock, scps.ElseBlock]]):
                last_scope_line.render()

            scope_line.write()
            last_scope_line = scope_line


    def get_function_template_signature(self):
        func_args = {**self.arguments}
        for key, val in self.arguments.items():
            if isinstance(val, ct.Template):
                # replace function argument templates with template types
                func_args[key] = val.value

        func_ret = self.return_type
        if isinstance(self.return_type, ct.Template):
            func_ret = self.return_type.value
        
        return func_args, func_ret
    
    def get_template_type(self, name:str):
        return self.template_types[self.get_template_index(name)]

    def get_mangled_name(self, template_types:list[ct.CompilerType] = []):
        mangled_name = f"{self.name}"
        if len(template_types) == 0:
            return mangled_name
        mangled_name += f"_tmp_{self.module.mangle_salt}_{f'_{self.module.mangle_salt}_'.join([tt.value._to_string() for tt in template_types])}"
        return mangled_name
    
    def append_operation(self, operation:Operation):
        operation.builder = self.builder
        return operation
    
    def append_scope(self, scope:scps.Scope):
        return self.builder.append_scope(scope)
    
        
    def __repr__(self) -> str:
        return self.function

    # functions used for debugging are prefixed with dbg
    def dbg_print(self, alias:str = None):
        if alias == None:
            alias = self.name
        print(self.function[alias])

    def dbg_print_module(self):
        print(self.module)