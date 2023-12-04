from llvmcompiler.compiler_types.types.lookup_label import LookupLabel
import llvmcompiler.tree_builder as tb
from llvmcompiler import StructDefinition, CompilerType,\
    I8Type, I32Type, C8Type,\
    F32Type, D64Type, I64Type,\
    BoolType, ArrayType, StructType,\
    StructPointerType, VoidType, Template, Module, FunctionDefinition,\
    FunctionReturnOperation, DefineOperation, Value, Operation, CallOperation,\
    AssignOperation, IndexOperation, TemplatePointer, CastOperation, DereferenceOperation,\
    TypeSizeOperation, FreeOperation, BreakOperation
from llvmcompiler.ir_renderers.operations import *
from more_itertools import peekable

class TokenIterator:
    def __init__(self, tokens:list[tb.Token]):
        self.tokens = tokens
        self.index = 0
        self.prepended:list[tb.Token] = []

    def __next__(self):
        return self.next()
    
    def next(self):
        result = None
        if len(self.prepended) > 0:
            result = self.prepended[len(self.prepended) - 1]
            self.prepended.pop()
        else:
            try:
                result = self.tokens[self.index]
                self.index += 1
            except IndexError:
                raise StopIteration
        return result
    
    def prepend(self, val:tb.Token):
        self.prepended.append(val)
    
    def current(self):
        result = self.tokens[self.index]
        return result

    def prev(self):
        if self.index-1 < 0:
            raise IndexError
        return self.tokens[self.index-1]

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return f"{self.prepended} + {self.tokens[self.index::]}"

    def dbg_print(self, dbgmsg:str):
        print(f"{dbgmsg}{[tok.value for tok in self.prepended] + [tok.value for tok in self.tokens[self.index::]]}")

class TreeBuilder:
    """
    This class is used to build the concrete syntax
    tree and spits out a module.
    """
    def __init__(self, token_list:list[tb.Token], file_name:str, program_salt = "MMAANNGGLLEE") -> None:
        self.token_list = TokenIterator(token_list)
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
        exporting = False
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.struct_keyword:
                    self.module_scope.append(self.context_struct_definition())

                case tb.SyntaxToken.func_keyword | tb.SyntaxToken.export_keyword:
                    if tok.type == tb.SyntaxToken.export_keyword:
                        exporting = True
                        continue
                    else:
                        self.module_scope.append(self.context_function_statement_definition([], exporting))
                        exporting = False

    def context_order_of_operations(self, templates:list[str]) -> (Operation, tb.Token):
        """
        This is the context for order of operations.

        returns a tuple containting (operation/value, last_token:Token)
        """
        operations = []
        current_op = [[],None]
        op_val_len = 2
        # functions to handle creation of potential operator list.
        def push_val(val:tb.Token):
            # this only works for rhs lhs operators, single side ops will need to be evaluated manually
            nonlocal current_op
            current_op[0].append(tb.OpValue(val))
            if len(current_op[0]) == op_val_len:
                operations.append(current_op)
                current_op = [[current_op[0][len(current_op[0])-1]], current_op[1]]
            
        def push_op(op:tb.Token, _op_val_len = 2):
            nonlocal op_val_len
            current_op[1] = op
            op_val_len = _op_val_len

        
        last_tok = None
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.label:
                label_ret = self.context_label_trunk(tok.value, templates)
                push_val(label_ret)
            elif tok.type.is_literal or tok.type.is_type:
                push_val(tok)
            elif tok.type.is_lhs_rhs_operator:
                push_op(tok)
                if tok.type == tb.SyntaxToken.cast_op:
                    push_val(self.context_type_trunk(templates))
            elif tok.type.is_single_arg_operator:
                push_val(self.context_single_argument_op(tok, templates))
            elif tok.type == tb.SyntaxToken.parentheses_start:
                push_val(self.context_order_of_operations(templates)[0])
            elif tok.type.is_ending_token:
                last_tok = tok
                break

        
        if len(operations) == 0 and len(current_op[0]) == 1:
            # push a single value.
            result = current_op[0][0].get_value()
            return (result, last_tok)
        
        if len(operations) != 0:
            op_order = tb.OperationsOrder([tb.PotentialOperation(*op) for op in operations])
            result = op_order.get_tree()
            return (result, last_tok)
        return (None, last_tok)
    
    def context_single_argument_op(self, op:tb.Token, templates:list[str]):
        print(f"CONTEXT_SINGLE_ARGUMENT {op}")
        def ret_operation(arg):
            match op.type:
                case tb.SyntaxToken.dereference_op:
                    return DereferenceOperation([arg])
                case tb.SyntaxToken.sizeof_op:
                    self.token_list.dbg_print("CREATE SIZE OF")
                    return TypeSizeOperation([arg])
                case tb.SyntaxToken.not_op:
                    return NotOperation([arg])
        
        if op.type == tb.SyntaxToken.sizeof_op:
            return TypeSizeOperation([self.context_type_trunk(templates)])

        for tok in self.token_list:
            if tok.type.is_single_arg_operator:
                return ret_operation(self.context_single_argument_op(tok, templates))
            elif tok.type.is_lhs_rhs_operator:
                print("Error: Expected argument after single argument operation, not LHS/RHS operator.")
            elif tok.type == tb.SyntaxToken.label:
                return ret_operation(self.context_label_trunk(tok.value, templates))


    def context_label_trunk(self, label:str, templates:list[str], dereferences = 0):
        template_args:list[tb.Token] = []
        function_args = []
        is_function = False
        label_product = label
        is_index = False
        index_args = []

        # helper function to add dereferences to lhs
        def prepend_derefs(instr):
            ret_ins = instr
            for _ in range(dereferences):
                ret_ins = DereferenceOperation([ret_ins])

            return ret_ins

        # helper function to call function
        def call_function(templates):
            
            # is a function but not a memeber function
            ooo_ret = self.context_order_of_operations(templates)
            if ooo_ret[0] != None:
                function_args.append(ooo_ret[0])
                
                while ooo_ret[1].type != tb.SyntaxToken.parentheses_end:
                    ooo_ret = self.context_order_of_operations(templates)
                    function_args.append(ooo_ret[0])
            print(f"""\nFUNCTION {{
    LABEL     = {label_product}
    ARGS      = {function_args}
    TEMPLATES = {template_args}
}}\n""")
            return CallOperation(label_product, function_args, template_args)
        
        for itteration, tok in enumerate(self.token_list):
            if tok.type == tb.SyntaxToken.function_call_template_op:
                # is a template function
                is_function = True
            elif (is_function or itteration == 0)\
            and tok.type == tb.SyntaxToken.parentheses_start:
                # is a function that may be a template function
                return prepend_derefs(call_function(templates))
            elif is_function and tok.type == tb.SyntaxToken.less_than_op:
                # Get the templates
                template_args = self.context_template(templates)
            elif not is_function:
                # is not a function
                if tok.type == tb.SyntaxToken.assign_op:
                    if is_index:
                        label_product = prepend_derefs(IndexOperation([label_product, *index_args]))
                    
                    ooo_ret = self.context_order_of_operations(templates)
                    print(f"ASSIGN OP {[label_product, ooo_ret[0]]}")
                    return AssignOperation([label_product, ooo_ret[0]])
                elif tok.type == tb.SyntaxToken.sqr_bracket_start:
                    is_index = True
                    ooo_ret = self.context_order_of_operations(templates)
        
                    index_args.extend([ooo_ret[0]])
                elif tok.type == tb.SyntaxToken.access_op:
                    is_index = True
                    
                elif tok.type == tb.SyntaxToken.label and is_index:
                    # is a label after an access operator
                    index_args.append(LookupLabel(tok.value))
                elif tok.type == tb.SyntaxToken.parentheses_start:
                    # call member function without templates
                    if is_index:
                        label_product = IndexOperation([label_product, *index_args])
                    
                    return prepend_derefs(call_function(templates))
                elif (tok.type.is_ending_token or tok.type.is_lhs_rhs_operator) and is_index:
                    # this is for if we reach an ending token
                    # BUG
                    self.token_list.prepend(tok)
                    print(f"LABEL RET {[label_product, *index_args]}")
                    return prepend_derefs(IndexOperation([label_product, *index_args]))
                elif tok.type.is_ending_token or tok.type.is_lhs_rhs_operator:
                    self.token_list.prepend(tok)
                    return prepend_derefs(label_product)
                elif tok.type == tb.SyntaxToken.cast_op and is_index:
                    return prepend_derefs(CastOperation([IndexOperation([label_product, *index_args]), self.context_type_trunk(templates)]))
                else:
                    return prepend_derefs(label_product)


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
        deref = 0

        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.dereference_op:
                    deref += 1
                    continue
                case tb.SyntaxToken.scope_end:
                    break
                case tb.SyntaxToken.let_keyword:
                    scope.append(self.context_define(templates))

                case tb.SyntaxToken.label:
                    scope.append(self.context_label_trunk(tok.value, templates, deref))
                    deref = 0
                case tb.SyntaxToken.return_op:
                    ret_val = self.context_order_of_operations(templates)
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
        def get_ptr(typ:CompilerType):
            if pointer > 0:
                for _ in range(pointer):
                    typ = typ.cast_ptr()
                return typ
            else:
                return typ
            
        pointer = 0
        array_args = []
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer += 1
            elif tok.type == tb.SyntaxToken.sqr_bracket_end:
                return get_ptr(ArrayType(*array_args))
            elif tok.type == tb.SyntaxToken.integer_literal:
                array_args.append(int(tok.value))
            elif tok.value == "x" if tok.type == tb.SyntaxToken.label else False:
                # This is a stylistic label in arrays, It has no type value.
                pass
            else:
                array_args.append(self.get_type(tok, templates, pointer))
                pointer = 0

    def context_template(self, templates:list[str]):
        pointer = 0
        type_templates:list[CompilerType] = []
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer += 1
            elif tok.type == tb.SyntaxToken.greater_than_op:
                break
            else:
                type_templates.append(self.get_type(tok, templates, pointer))
                pointer = 0
        
        return type_templates

    def context_type_struct(self, name:str, templates:list[str], pointer = 0) -> CompilerType:
        """
        Returns when an assignment, delimiter, or line_end (;) operator is reached
        """
        
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.less_than_op:
                temps = self.context_template(templates)
                if pointer > 0:
                    return StructPointerType(name, temps, ptr_count=pointer)
                else:
                    return StructType(name, temps)
            else:
                if pointer > 0:
                    return StructPointerType(name, ptr_count=pointer)
                else:
                    return StructType(name)

    def context_type_trunk(self, templates:list[str]) -> CompilerType:
        """
        Returns when the type is finished being read
        """
        # helper function to tell if it is a pointer type or not.
        
        pointer = 0
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.dereference_op:
                pointer += 1
            else:
                return self.get_type(tok, templates, pointer)
            
                
        
    def get_type(self, tok:tb.Token, templates:list[str], pointer = 0):

        def get_ptr(typ:CompilerType):
            if pointer > 0:
                for _ in range(pointer):
                    typ = typ.cast_ptr()
                return typ
            else:
                return typ

        match tok.type:
            case tb.SyntaxToken.sqr_bracket_start:
                return get_ptr(self.context_type_list(templates))
            
            case tb.SyntaxToken.label:
                if tok.value in self.struct_namespace:
                    return self.context_type_struct(tok.value, templates, pointer)
                elif tok.value in templates:
                    if pointer > 0:
                        return TemplatePointer(tok.value, ptr_count=pointer)
                    else:
                        return Template(tok.value)
            
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