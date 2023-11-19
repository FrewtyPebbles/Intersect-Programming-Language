from llvmcompiler.tree_builder import Token, SyntaxToken
from llvmcompiler import StructDefinition, CompilerType,\
    I8Type, I8PointerType, I32Type, I32PointerType, C8Type, C8PointerType,\
    F32Type, F32PointerType, D64Type, D64PointerType, I64Type, I64PointerType,\
    BoolType, BoolPointerType, ArrayType, ArrayPointerType, StructType,\
    StructPointerType, VoidType, Template, Module, FunctionDefinition, FunctionReturnOperation

class TreeBuilder:
    """
    This class is used to build the concrete syntax
    tree and spits out a module.
    """
    def __init__(self, token_list:list[Token], file_name:str, program_salt = "MMAANNGGLLEE") -> None:
        self.token_list = iter(token_list)
        self.module_scope = []
        self.file_name = file_name
        self.program_salt = program_salt
        self.struct_namespace:list[str] = []
        """
        `struct_namespace` stores the names of any structs when their name is read in their definition.
        This is so when the type trunk reaches a label it can reference it against the current templates
        and defined struct names and properly produce a type.
        """

    def get_module(self):
        """
        Returns the file as a module.
        """
        return Module(self.file_name, scope=self.module_scope, mangle_salt=self.program_salt)

    def parse_trunk(self):
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.struct_keyword:
                    self.context_struct_definition()

                case SyntaxToken.func_keyword | SyntaxToken.export_keyword:
                    if tok.type == SyntaxToken.export_keyword:
                        next(self.token_list)
                        self.context_function_statement_definition([], True)
                    else:
                        self.context_function_statement_definition([], False)

    def context_rhs_trunk(self, templates:list[str]):
        """
        This is the context trunk for the right hand side of an operator.
        """

    def context_lhs_trunk(self, templates:list[str]):
        """
        This is the context trunk for the left hand side of an assignment operator.

        NOTE: This is not used for `let` statements.
        """

    def context_declaration(self, templates:list[str]):
        """
        This is the context trunk for the left hand side of an assignment operator.

        NOTE: This is not used for `let` statements.
        """
    
    def context_scope_trunk(self, templates:list[str]):
        """
        This is where lines of code/scopes are parsed from.
        """
        scope = []
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.let_keyword:
                    scope.append(self.context_declaration(templates))

                case SyntaxToken.label:
                    scope.append(self.context_lhs_trunk(templates))
                
                case SyntaxToken.return_op:
                    scope.append(FunctionReturnOperation([self.context_rhs_trunk(templates)]))


    
    
    
    def context_template_definition(self) -> list[str]:
        templates = []
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.label:
                    templates.append(tok.value)
                case SyntaxToken.greater_than_op:
                    break
        
        return templates
    
    def context_function_statement_definition_arguments(self, templates:list[str]):
        arguments:dict[str, CompilerType] = {}
        argument_label_buffer = ""
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.label:
                    argument_label_buffer = tok.value
                case SyntaxToken.cast_op:
                    arguments[argument_label_buffer] = self.context_type_trunk(templates)
                    argument_label_buffer = ""
                case SyntaxToken.parentheses_end:
                    break
            
        return arguments

    def context_function_statement_definition(self, templates:list[str], extern = False):
        """
        This defines the statement part of the function.
        
        The scope of the function is handled by context_scope.
        """
        name = ""
        template_definition:list[str] = []
        scope = []
        return_type:CompilerType = None
        arguments:dict[str,CompilerType] = {}
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.label:
                    name = tok.value

                case SyntaxToken.less_than_op:
                    template_definition = self.context_template_definition()

                case SyntaxToken.parentheses_start:
                    arguments = self.context_function_statement_definition_arguments([*templates, *template_definition])

                case SyntaxToken.fn_specifier_op:
                    return_type = self.context_type_trunk([*templates, *template_definition])

                case SyntaxToken.scope_start:
                    scope = self.context_scope([*templates, *template_definition])
                    break
        
        return FunctionDefinition(name, arguments, return_type, False, template_definition, scope, extern=extern)
    
    def context_struct_definition(self):
        name = ""
        attributes = {}
        functions = []
        templates:list[str] = []

        # first parse the statement before the curly brackets to add struct
        # to the namespace and get the struct template names

        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.label:
                    name = tok.value
                case SyntaxToken.less_than_op:
                    templates = self.context_template_definition()
                    break
        
        # then parse the definition of the struct within the curly braces

        attribute_label_buffer = ""
        for tok in self.token_list:
            match tok.type:
                case SyntaxToken.label:
                    attribute_label_buffer = tok.value
                case SyntaxToken.cast_op:
                    attributes[attribute_label_buffer] = self.context_type_trunk(templates)
                    attribute_label_buffer = ""
                case SyntaxToken.func_keyword:
                    functions.append(self.context_function_statement_definition(templates))
                case SyntaxToken.scope_end:
                    break
                    


        return StructDefinition(name, attributes, functions, templates)


    def context_type_list(self, templates:list[str]) -> CompilerType:
        """
        Returns when an assignment, delimiter, or line_end (;) operator is reached
        """
        # helper function to tell if it is a pointer type or not.
        pointer = False
        array_args = []
        for tok in self.token_list:
            if tok.type == SyntaxToken.dereference_op:
                pointer = True
            elif tok.type == SyntaxToken.sqr_bracket_end:
                return ArrayType(*array_args)
            elif tok.value == "x" if tok.type == SyntaxToken.label else False:
                # This is a stylistic label in arrays, It has no type value.
                pass
            else:
                array_args.append(self.get_type(tok, templates, pointer))

    def context_template(self, templates:list[str]):
        pointer = False
        type_templates:list[CompilerType] = []
        for tok in self.token_list:
            if tok.type == SyntaxToken.dereference_op:
                pointer = True
            elif tok.type == SyntaxToken.greater_than_op:
                break
            else:
                type_templates.append(self.get_type(tok, templates, pointer))
                pointer = False
        
        return type_templates

    def context_type_struct(self, name:str, templates:list[str]) -> CompilerType:
        """
        Returns when an assignment, delimiter, or line_end (;) operator is reached
        """
        for tok in self.token_list:
            if tok.type == SyntaxToken.sqr_bracket_start:
                return StructType(name, self.context_template(templates))
            else:
                return StructType(name)

    def context_type_trunk(self, templates:list[str]) -> CompilerType:
        """
        Returns when the type is finished being read
        """
        # helper function to tell if it is a pointer type or not.
        
        pointer = False
        for tok in self.token_list:
            if tok.type == SyntaxToken.dereference_op:
                pointer = True
            else:
                return self.get_type(tok, templates, pointer)
            
                
        
    def get_type(self, tok:Token, templates:list[str], pointer = False):

        get_ptr = lambda typ: typ.cast_ptr() if pointer else typ

        match tok.type:
            case SyntaxToken.sqr_bracket_start:
                return get_ptr(self.context_type_list(templates))
            
            case SyntaxToken.label:
                if tok.value in self.struct_namespace:
                    return get_ptr(self.context_type_struct(tok.value, templates))
                elif tok.value in templates:
                    return Template(tok.value)
            
            case SyntaxToken.i8_type:
                return get_ptr(I8Type)
            
            case SyntaxToken.i32_type:
                return get_ptr(I32Type)
            
            case SyntaxToken.i64_type:
                return get_ptr(I64Type)
            
            case SyntaxToken.f32_type:
                return get_ptr(F32Type)
            
            case SyntaxToken.d64_type:
                return get_ptr(D64Type)
            
            case SyntaxToken.bool_type:
                return get_ptr(I32Type)
            
            case SyntaxToken.c8_type:
                return get_ptr(C8Type)