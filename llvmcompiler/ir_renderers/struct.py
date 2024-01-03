from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.modules as mod

class StructDefinition:
    """
    This is the definition of the struct.
    """
    def __init__(self, name:str, attributes:dict[str, ct.CompilerType] = None,
        functions:list[fn.FunctionDefinition] = None, templates:list[str] = None,
        module:mod.Module = None, packed = False, documentation = None, operatorfunctions:list[fn.FunctionDefinition] = None
    ) -> None:
        self.name = name
        self.attributes = {} if attributes == None else attributes
        self.functions = [] if functions == None else functions
        self.operatorfunctions = [] if operatorfunctions == None else operatorfunctions
        self.templates = [] if templates == None else templates
        self.module = module
        self.packed = packed

        self.struct_aliases:dict[str, Struct] = {}
        """
        This dict contains the mangled aliases.
        Use `get_struct` to retrieve/write and retrieve structs from/to this variable
        """
        self.documentation = {"purpose":""} if documentation == None else documentation

        #print(self.get_documentation())

    def __hash__(self) -> int:
        return hash(repr(self))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"functions", "operatorfunctions", "templates", "module", "attributes", "struct_aliases", "documentation"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result

    def get_documentation(self) -> str:
        ret_val = f"<div><h1 id=\"GOTO-STRUCT-{self.name}\">{self.name}"
        if self.templates != []:
            ret_val += f" < {', '.join(self.templates)} >"
        ret_val += "</h1>"
        ret_val += self.documentation["purpose"]
        ret_val += "<h3>Attributes</h3>"
        ret_val += "<ul>"
        for name, typ in self.attributes.items():
            type_str = f"<a href=\"#GOTO-STRUCT-{typ.name}\">{typ}</a>" if isinstance(typ, StructType) else f"{typ}"
            ret_val += f"<li id=\"GOTO-STRUCT-{self.name}-ATTR-{name}\">{name}: {type_str}</li>"
        ret_val += "</ul>"

        if len(self.operatorfunctions):
            ret_val += "<h3>Operators</h3>"
            ret_val += "<ul>"
            for func in self.operatorfunctions:
                ret_val += f"<li>{func.get_documentation()}</li>"
            ret_val += "</ul>"

        if len(self.functions):
            ret_val += "<h3>Methods</h3>"
            ret_val += "<ul>"
            for func in self.functions:
                ret_val += f"<li>{func.get_documentation()}</li>"
            ret_val += "</ul>"
        
        ret_val += "</div>"

        return ret_val

    
    def get_struct(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types
        mangled_name = self.get_mangled_name(template_types)
        if mangled_name in self.struct_aliases.keys():
            return self.struct_aliases[mangled_name]
        else:
            # make a new struct that potentially has templates
            new_struct = self.write(template_types)
            return new_struct
    
    def write(self, template_types:list[ct.CompilerType] = []):
        new_struct = Struct(template_types, self)
        self.struct_aliases[new_struct.name] = new_struct
        return new_struct.write()

    @lru_cache(32, True)
    def get_template_index(self, name:str):
        #print(name)
        #print(self.templates)
        return self.templates.index(name)    

    def get_mangled_name(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types
        mangled_name = self.name
        if len(template_types) == 0:
            return mangled_name
        
        mangled_name += f"_struct_tmp_{self.module.mangle_salt}_{f'_{self.module.mangle_salt}_'.join([tt.value._to_string() for tt in template_types])}"\
            .replace(f'\\22', '').replace(f'"', '')\
            .replace(f'%', '').replace(f'*', '')
        #print(f"MANG NAME {mangled_name}")
        return mangled_name



class Struct:
    """
    This is where the struct is rendered and contains the ir of the struct.
    The struct is rendered separately for name mangling purposes.
    """
    def __init__(self, template_types:list[ct.CompilerType], struct_definition:StructDefinition = None) -> None:
        self.struct_definition = struct_definition
        self.name = self.struct_definition.get_mangled_name(template_types)
        """
        Name is mangled.
        """
        #print(f"NAME : {self.name}")

        self.functions:dict[str, fn.FunctionDefinition] = {}
        self.operatorfunctions:dict[str, list[fn.FunctionDefinition]] = {}
        """
        This contains all of the `FunctionDefinition`(s) for the struct.
        """
        # TODO: BUG: Figure out how to mangle name without mangling original function definition, yet still retain information 
        for func in deepcopy(self.struct_definition.functions):
            func.struct = self
            func.module = self.struct_definition.module
            self.functions[func.name] = func
            
            #print(f"{self.name}->{func.name}")

            func.name = f"{self.name}_memberfunction_{func.name}"

        for func in deepcopy(self.struct_definition.operatorfunctions):
            clean_name = func.name.split("_arg_")[0]
            if clean_name not in self.operatorfunctions.keys():
                self.operatorfunctions[clean_name] = []
            func.struct = self
            func.module = self.struct_definition.module
            self.operatorfunctions[clean_name].append(func)
            
            #print(f"{self.name}->{clean_name}")

            func.name = f"{self.name}_memberfunction_{func.name}"

            

        

        self.raw_attributes:dict[str, ct.CompilerType] = deepcopy(self.struct_definition.attributes)
        """
        These are the attributes and their compiler types.
        """


        self.attributes:dict[str, vari.Value] = {}
        self.module = self.struct_definition.module
        
        self.size = 0
        self.template_types = template_types
        self.ir_struct = None

    def __hash__(self) -> int:
        return hash(repr(self))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"module", "struct_definition"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result

    @lru_cache(32, True)
    def get_template_type(self, name:str):
        index = self.struct_definition.get_template_index(name)
        typ = self.template_types[index]
        if isinstance(typ, ct.Template):
            typ = typ.get_template_type()
        return typ

    @lru_cache(32, True)
    def write(self):
        mangled_name = self.struct_definition.get_mangled_name(self.template_types)

        self.ir_struct = self.module.module.context.get_identified_type(mangled_name)
        
        self.link_raw_attributes()
        
        types = []
        for at_type_ind, (at_key, at_type) in enumerate(self.raw_attributes.items()):
            self.attributes[at_key] = vari.Value(ct.I32Type(), at_type_ind)
            types.append(at_type.value)
            self.size += at_type.size
        self.ir_struct.packed = self.struct_definition.packed
        self.ir_struct.set_body(*types)

        return self
    
    def link_raw_attributes(self):
        """
        This adds attributes parent and module to the attributes.
        """
        for key in self.raw_attributes.keys():
            
            self.raw_attributes[key].module = self.module
            self.raw_attributes[key].parent = self


    @lru_cache(32, True)
    def get_type(self, func:fn.Function):
        struct = StructType(self.struct_definition.name, self.template_types, self.module)
        struct.parent = func
        struct.ptr_count = 0
        return struct

    @lru_cache(32, True)
    def get_attribute(self, name:str, template_types:list[ct.CompilerType] = None, get_definition = False) -> fn.Function | vari.Value:
        """
        Gets an attribute on the struct.  (Includes member functions.)

        The attribute type is a Value.
        """
        template_types = [] if template_types == None else template_types

        
        attrs = {**self.attributes, **self.functions}
        # print(f"STRUCT METHS {self.functions.keys()}")
        try:
            attr = attrs[name]
            if isinstance(attr, fn.FunctionDefinition):
                if get_definition:
                    return attr
                else:
                    return attr.get_function(template_types)
            else:
                return attr
        except KeyError:
            definition_attrs = {"attributes":self.struct_definition.attributes, "functions":self.struct_definition.functions, "operators":self.struct_definition.operatorfunctions}
            print(f"Error: {name} is not a valid attribute of {self.struct_definition.name}!\n")

    @lru_cache(32, True)
    def get_operator(self, operator:str, get_definition = False, arg_type:ct.CompilerType = None, template_types:list[ct.CompilerType] = None) -> fn.Function | vari.Value:
        """
        Gets an attribute on the struct.  (Includes member functions.)

        The attribute type is a Value.
        """
        template_types = [] if template_types == None else template_types
        
        try:
            op = self.operatorfunctions[operator]
            
            for func in op:
                if len(func.arguments) > 2:
                    print("Error: Operators can only have 1-2 arguments.")
                elif len(func.arguments) == 0:
                    print("Error: Operators must have at least 1 self referencing argument.")
                elif len(func.arguments) == 1:
                    if get_definition:
                        return func
                    else:
                        return func.get_function(template_types)
                else:
                    other = [*func.arguments.keys()]
                    other.remove("self")
                    other = other[0]
                    if isinstance(func.arguments[other], type(arg_type)):
                        if get_definition:
                            return func
                        else:
                            return func.get_function(template_types)
            
        except KeyError:
            # OPERATOR NOT IMPLEMENTED
            return None
    

class StructType(ct.CompilerType):
    """
    This is the type reference to the struct.
    """
    def __init__(self, name:str, template_types:list[ct.CompilerType] = None, module:mod.Module = None, ptr_count = 0) -> None:
        self.module:mod.Module = module
        self.name = name
        self.template_types = [] if template_types == None else template_types
        self.templates_linked = False
        self._struct = None
        self._value = None
        self.ptr_count = ptr_count

    def __hash__(self) -> int:
        return hash(repr(self))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in {"module", "template_types", "_struct"}:
                setattr(result, k, v)
                continue
            setattr(result, k, deepcopy(v, memo))
        return result

    @property
    def struct(self) -> Struct:
        if not self.templates_linked:
            for tt in self.template_types:
                tt.module = self.module
                tt.parent = self.parent
            self.templates_linked = True
        if self._struct == None:
            self._struct = self.module.get_struct(self.name)\
                .get_struct(self.template_types)
        return self._struct

    @property
    def size(self):
        if not self.templates_linked:
            for tt in self.template_types:
                tt.module = self.module
                tt.parent = self.parent
            self.templates_linked = True
        return self.struct.size
    
    @property
    def value(self):
        if not self.templates_linked:
            for tt in self.template_types:
                tt.module = self.module
                tt.parent = self.parent
                self.templates_linked = True
        self._value = self.struct.ir_struct
        for pn in range(self.ptr_count):
            self._value = self._value.as_pointer()
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val

    def cast_ptr(self):
        self.ptr_count += 1
        return self

    def create_ptr(self):
        self_cpy = deepcopy(self)
        self_cpy.ptr_count += 1
        return self_cpy

    def create_deref(self):
        self_cpy = deepcopy(self)
        if self_cpy.ptr_count > 0:
            self_cpy.ptr_count -= 1
        return self_cpy
    
    
    def __repr__(self) -> str:
        ret_str = "$" * self.ptr_count
        ret_str += self.name
        if self.template_types != []:
            ret_str += f"&lt;{', '.join([f'{t_t}' for t_t in self.template_types])}&gt;"
        return ret_str