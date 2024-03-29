from __future__ import annotations
from typing import Dict, List, Union, TYPE_CHECKING
from llvmlite import ir
from functools import lru_cache
from copy import deepcopy

if TYPE_CHECKING:
    import llvmcompiler.ir_renderers.operations as op
    from llvmcompiler.modules.module import Module
    import llvmcompiler.ir_renderers.struct as st
    from llvmcompiler.ir_renderers.variable import Variable, Value
    from llvmcompiler.modules.module import Module

import llvmcompiler.compiler_types as ct
from llvmcompiler.ir_renderers.builder_data import BuilderData
from llvmcompiler.ir_renderers.scopes import IfBlock, ElseIfBlock, ElseBlock, Scope




class FunctionDefinition:
    def __init__(self, name:str, arguments:Dict[str, ct.CompilerType],
            return_type:ct.CompilerType, variable_arguments:bool = False, template_args:list[str] = None,
            scope:list[Scope | op.Operation] = None, struct:st.Struct = None, module:Module = None, extern = False,
            documentation = None, virtual = False):
        self.name = name
        if "_memberfunction_" in self.name:
            self.clean_name = self.name.split("_memberfunction_")[1]
        else:
            self.clean_name = self.name

        self.virtual = virtual
        self.arguments = arguments
        self.return_type = return_type
        self.variable_arguments = variable_arguments
        self.scope = [] if scope == None else scope
        self.template_args = [] if template_args == None else template_args
        self.struct = struct
        self.module = module
        self.extern = extern
        self.doc_data:dict[str, str | dict[str,str] | None] = {
            "purpose": None, # How this function should be used
            "implementation": None, # description of the implementation details of this function
            "args": {} # a description for each argument of the docstring
        } if documentation == None else documentation
        """
        This marks a function for external use for things like dlls.
        Just like extern "c" in c++.
        """

        self.function_aliases:dict[str, Function] = {}
        """
        This dict contains the mangled aliases.
        Use `get_function` to retrieve/write and retrieve functions from/to this variable
        """
    def __hash__(self) -> int:
        return hash(repr(self))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"module", "doc_data", "builder", "template_args", "scope", "function_aliases"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result

    def get_documentation(self) -> str:
        ret_val = "<div><h2>"
        if self.struct != None:
            ret_val += f"<a href=\"#GOTO-STRUCT-{self.struct.struct_definition.name}\">{self.struct.struct_definition.name}</a> . "
        ret_val += self.clean_name

        if t_a_len := len(self.template_args):
            ret_val += "< "
            for t_n, t_a in enumerate(self.template_args):
                ret_val += f"{t_a}"
                if t_n+1 != t_a_len:
                    ret_val += ", "
            ret_val += " >"
        
        ret_val += "("
        for a_name, arg in self.arguments.items():
            ret_val += f" {a_name}: {arg}"
            ret_val += ", "
        if len(self.arguments):
            ret_val = ret_val[:-2] + " "
        ret_val += f") ~> {self.return_type}</h2>"
        if self.doc_data['purpose'] != None:
            ret_val += f"<p>{self.doc_data['purpose']}</p>"
        if self.doc_data['args'] != {}:
            ret_val += "<h4>Arguments</h4><ul>"
            for key, val in self.doc_data['args'].items():
                ret_val += f"<li><b>{key}</b></br>"
                ret_val += f"{val}</li>"
            ret_val += "</ul>"
        if self.doc_data['implementation'] != None:
            ret_val += f"<p>{self.doc_data['implementation']}</p>"
        ret_val += "</div>"
        return ret_val


    def __repr__(self) -> str:
        return f"(FUNC : [{self.name}]<{self.template_args}>{self.arguments} ~> {self.return_type})"

    
    def get_function(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types

        mangled_name = self.get_mangled_name(template_types)
        if mangled_name in self.function_aliases.keys():
            return self.function_aliases[mangled_name]
        else:
            # make a new function that is potentially a template
            
            new_function = self.write(template_types)
            self.function_aliases[new_function.name] = new_function
            return new_function

    def write(self, template_types:list[ct.CompilerType] = None) -> Function:
        template_types = [] if template_types == None else template_types
        new_function = Function(template_types, self)
        return new_function.write()

    @lru_cache(32, True)
    def get_template_index(self, name:str):
        return self.template_args.index(name)    

    def get_mangled_name(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types
        mangled_name = f"{self.name}"

        if len(template_types) == 0:
            return mangled_name
        
        mangled_name += f"_tmp_{self.module.mangle_salt}_{f'_{self.module.mangle_salt}_'.join([tt.value._to_string() for tt in template_types])}"\
            .replace(f'\\22', '').replace(f'"', '')\
            .replace(f'%', '').replace(f'*', '')
        return mangled_name
    
class CFunctionDefinition(FunctionDefinition):
    def __init__(self, ir_function:ir.Function, return_type = None):
        self.ir_function = ir_function
        self.name = self.ir_function.name
        self.return_type = return_type
    
    def get_function(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types
        return CFunction(self)
    


class Function:
    def __init__(self, template_types:list[ct.CompilerType], function_definition:FunctionDefinition) -> None:
        self.template_types = template_types
        self.is_template_function = len(self.template_types) > 0
        self.function_definition = function_definition
        self.module = self.function_definition.module
        self.name = self.function_definition.get_mangled_name(template_types)
        "Name is mangled."

        self.function:ir.Function = None
        self.variables:Dict[str, Variable] = [{}]
        "This is all variables within the function scope."

        self.arguments = self.function_definition.arguments
        self.return_type = self.function_definition.return_type
        for key in self.arguments.keys():
            self.arguments[key].parent = self
            self.arguments[key].module = self.module
                

    def __repr__(self) -> str:
        return str(self.function)

    @lru_cache(32, True)
    def get_template_type(self, name:str):
        try:
            #print(f"FUNC TEMP {self.name} :: {name}")
            typ = self.template_types[self.function_definition.get_template_index(name)]
            if isinstance(typ, ct.Template):
                typ = typ.get_template_type()
            return typ
        except ValueError:
            try:
                #print(f"STRUCT TEMP {self.name} :: {name}")
                typ = self.function_definition.struct.get_template_type(name)
                if isinstance(typ, ct.Template):
                    typ = typ.get_template_type()
                return typ
            except KeyError:
                print(f"Error: {name} is not a valid template of {self.function_definition.struct.struct_definition.name}.")
            except TypeError:
                print(f"Error: {name} is not a valid template of {self.function_definition.name}.")
        

    def write(self) -> Function:

        func_args, func_ret = self.get_function_template_signature()

        
        self.function_type = ir.FunctionType(func_ret.value, [stype.value for stype in func_args.values()], var_arg=self.function_definition.variable_arguments)

        self.function:ir.Function = ir.Function(self.module.module, self.function_type, self.name)
        
        # name the function arguments
        for arg_num, arg in enumerate(func_args.keys()):
            self.function.args[arg_num].name = arg
        
        # get a ir cursor for writing ir to different things in the function
        self.entry = self.function.append_basic_block("entry")
        self.builder = BuilderData(self, ir.IRBuilder(self.entry), self.variables)
        self.builder.declare_arguments()
        # This cursor needs to be passed to any ir building classes that are used
        # within this function.

        self.get_variable = self.builder.get_variable


        # write the scope
        self.write_scope()
        
        return self

    @lru_cache(32, True)
    def get_function_template_signature(self):
        for key in self.arguments.keys():
            self.arguments[key].parent = self
            self.arguments[key].module = self.module

        func_args = self.arguments
        for key in self.arguments.keys():
            func_args[key].parent = self
            func_args[key].module = self.module

        func_ret = self.return_type
        self.return_type.parent = self
        self.return_type.module = self.module
        func_ret = self.return_type

        
        return func_args, func_ret

    def write_scope(self):
        last_scope_line = None
        for scope_line in deepcopy(self.function_definition.scope):
            scope_line.builder = self.builder

            if any([isinstance(last_scope_line, iftype1) for iftype1 in [IfBlock, ElseIfBlock]])\
            and any([isinstance(scope_line, iftype2) for iftype2 in [ElseIfBlock, ElseBlock]]):
                scope_line.prev_if = last_scope_line
            elif any([isinstance(last_scope_line, iftype1) for iftype1 in [IfBlock, ElseIfBlock, ElseBlock]])\
            and not any([isinstance(scope_line, iftype2) for iftype2 in [ElseIfBlock, ElseBlock]]):
                last_scope_line.render()
            scope_line.write()
            last_scope_line = scope_line
        if any([isinstance(last_scope_line, iftype1) for iftype1 in [IfBlock, ElseIfBlock, ElseBlock]]):
            last_scope_line.render()


    def create_operation(self, operation:op.Operation):
        operation.builder = self.builder
        return operation
    
        
class CFunction(Function):
    def __init__(self, function_definition:CFunctionDefinition):
        self.function_definition = function_definition
        self.function = self.function_definition.ir_function
        self.name = self.function_definition.name
        self.return_type = self.function_definition.return_type


