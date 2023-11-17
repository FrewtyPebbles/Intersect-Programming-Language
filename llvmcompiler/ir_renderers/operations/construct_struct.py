from llvmcompiler.compiler_types.type import CompilerType
from ..operation import Operation, arg_type
from llvmlite import ir
import llvmcompiler.ir_renderers.variable as vari
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from llvmcompiler.ir_renderers.function import FunctionDefinition
from llvmcompiler.ir_renderers.struct import StructType

class ConstructStructOperation(Operation):
    """
    This is used to construct structs.
    """
    def __init__(self, name:str, attributes:dict[str, arg_type], template_arguments:list[CompilerType] = [], heap = False) -> None:
        self.name = name
        self.attributes:dict[str, ir.Type | ir.Instruction] = attributes
        """
        This is where the attributes are stored and should be read from.
        """
        self.raw_arguments = [*attributes.values()]
        """
        The values of the attributes are temporarily stored in raw_arguments so
        they can be processed in the derived function "write_arguments".
        """
        self.arguments = [*attributes.values()]
        """
        The values of the attributes are stored in arguments after the 
        "write_arguments" derived function runs before "_write".
        """
        self.template_arguments = template_arguments  
    
    def create_attributes(self):
        for kn, key in enumerate(self.attributes.keys()):
            self.attributes[key].parent = self.builder.function
            self.attributes[key].builder = self.builder
            self.attributes[key].module = self.builder.module
            self.attributes[key] = self.process_arg(self.arguments[kn])

        for tempn in range(len(self.template_arguments)):

            self.template_arguments[tempn].parent = self.builder.function
            self.template_arguments[tempn].builder = self.builder
            self.template_arguments[tempn].module = self.builder.module

    def _write(self):
        self.builder.cursor.comment("OP::construct:struct START")
        # cast the arguments
        self.create_attributes()

        struct = self.builder.module.get_struct(self.name).get_struct(self.template_arguments)

        struct_alloca = self.builder.alloca(struct.ir_struct)
        for key, val in self.attributes.items():
            pointer = self.builder.cursor.gep(struct_alloca, [ir.IntType(32)(0), struct.get_attribute(key).get_value()], inbounds=True)
            self.builder.cursor.store(val, pointer)
        

        self.builder.cursor.comment("OP::construct:struct end")

        ret = vari.Value(StructType(self.name, self.template_arguments, self.builder.module), self.builder.cursor.load(struct_alloca), True)
        ret.parent = self.builder.function
        ret.builder = self.builder
        ret.module = self.builder.module
        return ret