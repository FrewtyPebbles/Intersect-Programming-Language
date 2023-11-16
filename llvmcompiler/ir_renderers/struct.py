from __future__ import annotations
import llvmcompiler.compiler_types as ct
import llvmcompiler.ir_renderers.function as fn
import llvmcompiler.ir_renderers.variable as vari
import llvmcompiler.modules as mod

class StructDefinition:
    """
    This is the definition of the struct.
    """
    def __init__(self, name:str, attributes:dict[str, ct.CompilerType] = {},
        functions:dict[fn.FunctionDefinition] = [], templates:list[str] = [],
        module:mod.Module = None, packed = False
    ) -> None:
        self.name = name
        self.attributes = attributes
        self.functions = functions
        self.templates = templates
        self.module = module
        self.packed = packed

        self.struct_aliases:dict[str, Struct] = {}
        """
        This dict contains the mangled aliases.
        Use `get_struct` to retrieve/write and retrieve structs from/to this variable
        """

    def get_struct(self, template_types:list[ct.CompilerType] = []):
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
            self.functions[func.name] = func

        self.raw_attributes:dict[str, ct.CompilerType] = {**self.struct_definition.attributes}
        """
        These are the attributes and their compiler types.
        """


        self.attributes:dict[str, vari.Value] = {}
        self.module = self.struct_definition.module
        
        self.size = 0
        self.template_types = template_types

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
        Also changes any attributes that are referencing its own type to a pointer.
        """
        for key in self.raw_attributes.keys():
            
            self.raw_attributes[key].module = self.module
            self.raw_attributes[key].parent = self

            attr = self.raw_attributes[key]
            if isinstance(attr, StructType):
                if attr.struct.struct_definition.name == self.struct_definition.name:
                    self.raw_attributes[key] = self.raw_attributes[key].cast_ptr()

    def get_attribute(self, name:str, template_types:list[ct.CompilerType] = []) -> fn.Function | ct.CompilerType:
        attrs = {**self.attributes, **self.functions}
        try:
            attr = attrs[name]
            if isinstance(attr, fn.FunctionDefinition):
                return attr.get_function(template_types)
            else:
                return attr
        except KeyError:
            print(f"Error: {name} is not a valid attribute of {self.struct_definition.name}!")

class StructType(ct.CompilerType):
    """
    This is the type reference to the struct.
    """
    def __init__(self, name:str, template_types:list[ct.CompilerType] = [], module:mod.Module = None) -> None:
        self.module = module
        self.name = name
        self.template_types = template_types

    @property
    def struct(self):
        return self.module.get_struct(self.name)\
            .get_struct(self.template_types)

    @property
    def size(self):
        return self.struct.size
    
    @property
    def value(self):
        return self.struct.ir_struct
    
    def cast_ptr(self):
        return StructPointerType(self.name, self.template_types, self.module)
    
class StructPointerType(StructType):
    """
    This is the type reference to the struct.
    """
    
    @property
    def value(self):
        return self.struct.ir_struct.as_pointer()

