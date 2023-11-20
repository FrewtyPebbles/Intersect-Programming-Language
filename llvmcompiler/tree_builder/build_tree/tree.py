import llvmcompiler.tree_builder as tb
from llvmcompiler import StructDefinition, CompilerType,\
    I8Type, I8PointerType, I32Type, I32PointerType, C8Type, C8PointerType,\
    F32Type, F32PointerType, D64Type, D64PointerType, I64Type, I64PointerType,\
    BoolType, BoolPointerType, ArrayType, ArrayPointerType, StructType,\
    StructPointerType, VoidType, Template, Module, FunctionDefinition,\
    FunctionReturnOperation, DefineOperation, Value, Operation, CallOperation,\
    AssignOperation



class TreeBuilder:
    """
    This class is used to build the concrete syntax
    tree and spits out a module.
    """
    def __init__(self, token_list:list[tb.Token], file_name:str, program_salt = "MMAANNGGLLEE") -> None:
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
                case tb.SyntaxToken.struct_keyword:
                    self.module_scope.append(self.context_struct_definition())

                case tb.SyntaxToken.func_keyword | tb.SyntaxToken.export_keyword:
                    if tok.type == tb.SyntaxToken.export_keyword:
                        next(self.token_list)
                        self.module_scope.append(self.context_function_statement_definition([], True))
                    else:
                        self.module_scope.append(self.context_function_statement_definition([], False))

    def context_order_of_operations(self, templates:list[str]) -> (Operation, tb.Token):
        """
        This is the context for order of operations.

        returns a tuple containting (operation/value, last_token:Token)
        """
        operations = []
        current_op = [[],None]
        # functions to handle creation of potential operator list.
        def push_val(val:tb.Token):
            # this only works for rhs lhs operators, single side ops will need to be evaluated manually
            nonlocal operations
            nonlocal current_op
            current_op[0].append(tb.OpValue(val))
            if len(current_op[0]) == 2:
                operations.append(current_op)
                current_op = [[current_op[0][1]], current_op[1]]
            
        def push_op(op:tb.Token):
            nonlocal current_op
            current_op[1] = op
        
        last_tok = None
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.label:
                label_ret = self.context_label_trunk(tok.value, templates)
                if isinstance(label_ret, tb.Token):
                    push_val(tok)
                    if label_ret.type in {tb.SyntaxToken.line_end, tb.SyntaxToken.parentheses_end,\
                    tb.SyntaxToken.delimiter}:
                        last_tok = tok
                        break
                    else:
                        push_op(label_ret)
                else:
                    push_val(label_ret)
            elif tok.type.is_literal or tok.type.is_type:
                push_val(tok)
            elif tok.type.is_lhs_rhs_operator:
                push_op(tok)
                if tok.type == tb.SyntaxToken.cast_op:
                    push_val(self.context_type_trunk(templates))
            elif tok.type == tb.SyntaxToken.parentheses_start:
                push_val(self.context_order_of_operations(templates)[0])
            elif tok.type in {tb.SyntaxToken.line_end, tb.SyntaxToken.parentheses_end,\
            tb.SyntaxToken.delimiter}:
                last_tok = tok
                break

        if len(operations) == 0 and len(current_op[0]) == 1:
            print(f"ORDER OF OPS INPUT : {[current_op]}")
            # push a single value.
            result = current_op[0][0].get_value()
            print(f"ORDER OF OPS RES : {result}")
            return (result, last_tok)
        print(f"ORDER OF OPS INPUT : {operations}")
        op_order = tb.OperationsOrder([tb.PotentialOperation(*op) for op in operations])
        result = op_order.get_tree()
        print(f"ORDER OF OPS RES : {result}")
        return (result, last_tok)
    
    def context_label_trunk(self, label:str, templates:list[str]):
        template_args:list[tb.Token] = []
        function_args = []
        is_function = False
        lhs = label
        for itteration, tok in enumerate(self.token_list):
            if tok.type == tb.SyntaxToken.function_call_template_op:
                is_function = True
            elif (is_function or itteration == 0)\
            and tok.type == tb.SyntaxToken.parentheses_start:
                is_function = True
                ooo_ret = self.context_order_of_operations(templates)
                function_args.append(ooo_ret[0])
                while ooo_ret[1].type == tb.SyntaxToken.delimiter:
                    ooo_ret = self.context_order_of_operations(templates)
                    function_args.append(ooo_ret[0])

                return CallOperation(label, function_args, template_args)
            
            elif is_function and tok.type == tb.SyntaxToken.less_than_op:
                template_args = self.context_template(templates)
            elif not is_function:
                if tok.type == tb.SyntaxToken.assign_op:
                    ooo_ret = self.context_order_of_operations(templates)
        
                    return AssignOperation([lhs, ooo_ret[0]])
                return tok


    def context_define(self, templates:list[str]):
        """
        This is the context trunk for the left hand side of an assignment operator.

        NOTE: This is not used for `let` statements.
        """
        name = ""
        typ = None
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    name = tok.value
                case tb.SyntaxToken.cast_op:
                    typ = self.context_type_trunk(templates)

                case tb.SyntaxToken.assign_op:
                    ooo_ret = self.context_order_of_operations(templates)

                    return DefineOperation([name, ooo_ret[0]])

                case tb.SyntaxToken.line_end:
                    # if there is no assignment operator, then the line_end token will
                    # not be consumed and this block will execute.
                    # This allocates a variable without assigning a value.
                    return DefineOperation([name, Value(typ)])

    
    def context_scope_trunk(self, templates:list[str]):
        """
        This is where lines of code/scopes are parsed from.
        """
        scope = []
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.scope_end:
                    break
                case tb.SyntaxToken.let_keyword:
                    scope.append(self.context_define(templates))

                case tb.SyntaxToken.label:
                    scope.append(self.context_label_trunk(tok.value, templates))
                case tb.SyntaxToken.return_op:
                    ret_val = self.context_order_of_operations(templates)
                    print(f"RETURN OP = {ret_val}")
                    if ret_val[0] == None:
                        scope.append(FunctionReturnOperation())
                    else:
                        scope.append(FunctionReturnOperation([ret_val[0]]))
        
        return scope


    
    
    
    def context_template_definition(self) -> list[str]:
        templates = []
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    templates.append(tok.value)
                case tb.SyntaxToken.greater_than_op:
                    break
        
        return templates
    
    def context_function_statement_definition_arguments(self, templates:list[str]):
        arguments:dict[str, CompilerType] = {}
        argument_label_buffer = ""
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    argument_label_buffer = tok.value
                case tb.SyntaxToken.cast_op:
                    arguments[argument_label_buffer] = self.context_type_trunk(templates)
                    argument_label_buffer = ""
                case tb.SyntaxToken.parentheses_end:
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
        return_type:CompilerType = VoidType()
        arguments:dict[str,CompilerType] = {}
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    name = tok.value

                case tb.SyntaxToken.less_than_op:
                    template_definition = self.context_template_definition()

                case tb.SyntaxToken.parentheses_start:
                    arguments = self.context_function_statement_definition_arguments([*templates, *template_definition])

                case tb.SyntaxToken.fn_specifier_op:
                    return_type = self.context_type_trunk([*templates, *template_definition])

                case tb.SyntaxToken.scope_start:
                    scope = self.context_scope_trunk([*templates, *template_definition])
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
                case tb.SyntaxToken.label:
                    name = tok.value
                case tb.SyntaxToken.less_than_op:
                    templates = self.context_template_definition()
                    break
            
        self.struct_namespace.append(name)
        
        # then parse the definition of the struct within the curly braces

        attribute_label_buffer = ""
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    attribute_label_buffer = tok.value
                case tb.SyntaxToken.cast_op:
                    attributes[attribute_label_buffer] = self.context_type_trunk(templates)
                    attribute_label_buffer = ""
                case tb.SyntaxToken.func_keyword:
                    functions.append(self.context_function_statement_definition(templates))
                case tb.SyntaxToken.scope_end:
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
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer = True
            elif tok.type == tb.SyntaxToken.sqr_bracket_end:
                return ArrayType(*array_args)
            elif tok.type == tb.SyntaxToken.integer_literal:
                array_args.append(int(tok.value))
            elif tok.value == "x" if tok.type == tb.SyntaxToken.label else False:
                # This is a stylistic label in arrays, It has no type value.
                pass
            else:
                array_args.append(self.get_type(tok, templates, pointer))
                pointer = False

    def context_template(self, templates:list[str]):
        pointer = False
        type_templates:list[CompilerType] = []
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer = True
            elif tok.type == tb.SyntaxToken.greater_than_op:
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
            if tok.type == tb.SyntaxToken.less_than_op:
                temps = self.context_template(templates)
                return StructType(name, temps)
            else:
                return StructType(name)

    def context_type_trunk(self, templates:list[str]) -> CompilerType:
        """
        Returns when the type is finished being read
        """
        # helper function to tell if it is a pointer type or not.
        
        pointer = False
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer = True
            else:
                return self.get_type(tok, templates, pointer)
            
                
        
    def get_type(self, tok:tb.Token, templates:list[str], pointer = False):

        get_ptr = lambda typ: typ.cast_ptr() if pointer else typ

        match tok.type:
            case tb.SyntaxToken.sqr_bracket_start:
                return get_ptr(self.context_type_list(templates))
            
            case tb.SyntaxToken.label:
                if tok.value in self.struct_namespace:
                    return get_ptr(self.context_type_struct(tok.value, templates))
                elif tok.value in templates:
                    return get_ptr(Template(tok.value))
            
            case tb.SyntaxToken.i8_type:
                return get_ptr(I8Type())
            
            case tb.SyntaxToken.i32_type:
                return get_ptr(I32Type())
            
            case tb.SyntaxToken.i64_type:
                return get_ptr(I64Type())
            
            case tb.SyntaxToken.f32_type:
                return get_ptr(F32Type())
            
            case tb.SyntaxToken.d64_type:
                return get_ptr(D64Type())
            
            case tb.SyntaxToken.bool_type:
                return get_ptr(I32Type())
            
            case tb.SyntaxToken.c8_type:
                return get_ptr(C8Type())