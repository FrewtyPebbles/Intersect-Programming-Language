from __future__ import annotations
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.modules as mod
from copy import deepcopy

class StructDefinition:
    """
    This is the definition of the struct.
    """
    def __init__(self, name:str, attributes:dict[str, ct.CompilerType] = {},
        functions:dict[fn.FunctionDefinition] = None, templates:list[str] = None,
        module:mod.Module = None, packed = False
    ) -> None:
        self.name = name
        self.attributes = attributes
        self.functions = [] if functions == None else functions
        self.templates = [] if templates == None else templates
        self.module = module
        self.packed = packed

        self.struct_aliases:dict[str, Struct] = {}
        """
        This dict contains the mangled aliases.
        Use `get_struct` to retrieve/write and retrieve structs from/to this variable
        """

    def get_struct(self, template_types:list[ct.CompilerType] = None):
        template_types = [] if template_types == None else template_types
        mangled_name = self.get_mangled_name(template_types)
        if mangled_name in self.struct_aliases.keys():
            return self.struct_aliases[mangled_name]
        else:
            # make a new struct that potentially has templates
            new_struct = self.write(template_types)
            self.struct_aliases[new_struct.name] = new_struct
            return new_struct
    
    def write(self, template_types:list[ct.CompilerType] = []):
        new_struct = Struct(template_types, self)
        return new_struct.write()

    def get_template_index(self, name:str):
        return self.templates.index(name)    

    def get_mangled_name(self, template_types:list[ct.CompilerType] = []):
        mangled_name = f"{self.name}"
        if len(template_types) == 0:
            return mangled_name
        
        mangled_name += f"_struct_tmp_{self.module.mangle_salt}_{f'_{self.module.mangle_salt}_'.join([tt.value._to_string() for tt in template_types])}"
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

        self.functions:dict[str, fn.FunctionDefinition] = {}
        """
        This contains all of the `FunctionDefinition`(s) for the struct.
        """
        for func in [*self.struct_definition.functions]:
            func.struct = self
            func.module = self.struct_definition.module
            self.functions[func.name] = func
            func.name = f"{self.name}_memberfunction_{func.name}"

        self.raw_attributes:dict[str, ct.CompilerType] = {**self.struct_definition.attributes}
        """
        These are the attributes and their compiler types.
        """


        self.attributes:dict[str, vari.Value] = {}
        self.module = self.struct_definition.module
        
        self.size = 0
        self.template_types = template_types
        self.ir_struct = None

    def get_template_type(self, name:str):
        typ = self.template_types[self.struct_definition.get_template_index(name)]
        if isinstance(typ, ct.Template):
            typ = typ.get_template_type()
        return typ

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

            # attr = self.raw_attributes[key]
            # if isinstance(attr, StructType):
            #     if attr.struct.struct_definition.name == self.struct_definition.name:
            #         self.raw_attributes[key] = self.raw_attributes[key].create_ptr()

    def get_type(self, func:fn.Function):
        struct = StructType(self.name, self.template_types, self.module)
        struct.parent = func
        return struct

    def get_attribute(self, name:str, template_types:list[ct.CompilerType] = [], get_definition = False) -> fn.Function | vari.Value:
        """
        Gets an attribute on the struct.  (Includes member functions.)

        The attribute type is a Value.
        """
        attrs = {**self.attributes, **self.functions}
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
            definition_attrs = {"attributes":self.struct_definition.attributes, "functions":self.struct_definition.functions}
            print(f"Error: {name} is not a valid attribute of {self.struct_definition.name}!\n The valid attributes are:\n{definition_attrs}")

class StructType(ct.CompilerType):
    """
    This is the type reference to the struct.
    """
    def __init__(self, name:str, template_types:list[ct.CompilerType] = [], module:mod.Module = None) -> None:
        self.module:mod.Module = module
        self.name = name
        self.template_types = template_types
        self.templates_linked = False

    @property
    def struct(self) -> Struct:
        if not self.templates_linked:
            for tt in self.template_types:
                tt.module = self.module
                tt.parent = self.parent
                self.templates_linked = True
        return self.module.get_struct(self.name)\
            .get_struct(self.template_types)

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
        return self.struct.ir_struct
    
    @value.setter
    def value(self, val):
        self.struct.ir_struct = val

    def cast_ptr(self):
        struct = StructPointerType(self.name, self.template_types, self.module, 1)
        struct.parent = self.parent
        return struct
    
    
    def __repr__(self) -> str:
        return f"(STRUCT TYPE : {{name: {self.name}, templates_types: {self.template_types}}})"
    
class StructPointerType(StructType):
    """
    This is the type reference to the struct.
    """
    def __init__(self, name: str, template_types: list[ct.CompilerType] = [], module: mod.Module = None, ptr_count = 0) -> None:
        super().__init__(name, template_types, module)
        self.ptr_count = ptr_count
        self._value = None
    
    @property
    def value(self):
        if self._value == None:
            self._value = deepcopy(self.struct.ir_struct)
            for pn in range(self.ptr_count):
                self._value = self._value.as_pointer()
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = value

    def cast_ptr(self):
        self.ptr_count += 1
        return self
    
    def __repr__(self) -> str:
        return f"(STRUCT PTR TYPE : {{name: {self.name}, templates_types: {self.template_types}, pointers: {self.ptr_count}}})"
        
