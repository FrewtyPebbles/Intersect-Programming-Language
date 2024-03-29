from llvmcompiler.compiler_types.types.lookup_label import LookupLabel
import llvmcompiler.tree_builder as tb
from llvmcompiler import StructDefinition, CompilerType,\
    I8Type, I32Type, C8Type,\
    F32Type, D64Type, I64Type,\
    BoolType, ArrayType, StructType,\
    VoidType, Template, Module, FunctionDefinition,\
    FunctionReturnOperation, DefineOperation, Value, Operation, CallOperation,\
    AssignOperation, IndexOperation, CastOperation, DereferenceOperation,\
    TypeSizeOperation, FreeOperation, BreakOperation, IfBlock, ElseIfBlock, ElseBlock, WhileLoop,\
    BreakOperation, AddressOperation
from llvmcompiler.ir_renderers.operations import *

import llvmcompiler.compiler_errors as ce

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
            result = self.prepended[-1]
            self.prepended.pop()
        else:
            try:
                result = self.tokens[self.index]
                self.index += 1
            except IndexError:
                raise StopIteration
        return result
    
    def peek_next(self):
        result = None
        if len(self.prepended) > 1:
            result = self.prepended[-2]
        else:
            try:
                result = self.tokens[self.index+1]
            except IndexError:
                raise StopIteration
        return result
    
    def prepend(self, val:tb.Token):
        self.prepended.append(val)
    
    def current(self):
        try:
            return self.prepended[-1]
        except:           
            return self.tokens[self.index]

    def prev(self):
        
        return self.tokens[self.index-2]

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return f"{self.prepended} + {self.tokens[self.index::]}"

    def dbg_print(self, dbgmsg:str):
        print(f"{dbgmsg}{[tok.value for tok in self.prepended] + [tok.value for tok in self.tokens[self.index::]]}")

class StructOption:
    """
    This is the type used in the struct namespace that is compared against when checking if a struct exists.
    """
    def __init__(self, name:str, templates:list[str]) -> None:
        self.name = name
        self.templates = templates

    @property
    def has_templates(self):
        return len(self.templates) != 0

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.name
        return other == self

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
        self.struct_namespace:list[StructOption] = []
        """
        `struct_namespace` stores the names of any structs when their name is read in their definition.
        This is so when the type trunk reaches a label it can reference it against the current templates
        and defined struct names and properly produce a type.
        """
        self.dbg_scope_padding = 0

    def dbg_print(self, msg:str):
        pass#print(f"{'    '*self.dbg_scope_padding}{msg}")

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
                    self.dbg_print("STRUCT:")
                    self.dbg_scope_padding += 1
                    self.module_scope.append(self.context_struct_definition())
                    self.dbg_scope_padding -= 1

                case tb.SyntaxToken.func_keyword | tb.SyntaxToken.export_keyword:
                    if tok.type == tb.SyntaxToken.export_keyword:
                        
                        exporting = True
                        continue
                    else:
                        self.dbg_print("FUNCTION:")
                        self.dbg_scope_padding += 1
                        func = self.context_function_statement_definition([], exporting)
                        self.dbg_scope_padding -= 1
                        # print(func)
                        self.module_scope.append(func)
                        exporting = False

    def context_order_of_operations(self, templates:list[str]) -> (Operation, tb.Token):
        """
        This is the context for order of operations.

        returns a tuple containting (operation/value, last_token:Token)
        """
        self.dbg_scope_padding += 1
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
                current_op = [[current_op[0][-1]], current_op[1]]
            
        def push_op(op:tb.Token, _op_val_len = 2):
            nonlocal op_val_len
            current_op[1] = op
            op_val_len = _op_val_len

        self.dbg_print(f"OOO .current {self.token_list.current()}")
        last_tok = None
        for tok in self.token_list:
            self.dbg_print(f"\tOOO > {tok}")
            if tok.type == tb.SyntaxToken.label:
                
                label_ret = self.context_label_trunk(tok.value, templates)
                self.dbg_print(f"\t\tOOO label {label_ret}")
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
            elif tok.type == tb.SyntaxToken.sqr_bracket_start or tok.type == tb.SyntaxToken.access_op or tok.type == tb.SyntaxToken.dereference_access_op:
                self.token_list.prepend(tok)
                current_op[0][0] = tb.OpValue(self.context_label_trunk(current_op[0][0].get_value(), templates, 0))
            elif tok.type.is_ending_token:
                last_tok = tok
                break
        
        self.dbg_scope_padding -= 1
        if len(operations) == 0 and len(current_op[0]) == 1:
            # push a single value.
            result = current_op[0][0].get_value()
            #print(f"NO ORDERING {result}")
            return (result, last_tok)
        
        if len(operations) != 0:
            op_order = tb.OperationsOrder([tb.PotentialOperation(*op) for op in operations])
            result = op_order.get_tree()
            #print(result)
            return (result, last_tok)
        return (None, last_tok)
    
    
    
    def context_single_argument_op(self, op:tb.Token, templates:list[str]):
        #print(f"CONTEXT_SINGLE_ARGUMENT {op}")
        def ret_operation(arg):
            match op.type:
                case tb.SyntaxToken.dereference_op:
                    return DereferenceOperation([arg], token=self.token_list.prev())
                case tb.SyntaxToken.sizeof_op:
                    return TypeSizeOperation([arg], token=self.token_list.prev())
                case tb.SyntaxToken.not_op:
                    return NotOperation([arg], token=self.token_list.prev())
                case tb.SyntaxToken.address_op:
                    return AddressOperation([arg], token=self.token_list.prev())
        
        if op.type == tb.SyntaxToken.sizeof_op:
            
            if self.token_list.current().type == tb.SyntaxToken.macro_delimiter_op:
                next(self.token_list)
                return TypeSizeOperation([self.context_type_trunk(templates)], token=self.token_list.prev())
            else:
                ooo = self.context_order_of_operations(templates)[0]
                self.token_list.prepend(self.token_list.prev())
                return TypeSizeOperation([ooo], token=self.token_list.prev())

        for tok in self.token_list:
            if tok.type.is_single_arg_operator:
                return ret_operation(self.context_single_argument_op(tok, templates))
            elif tok.type.is_lhs_rhs_operator:
                ce.CompilerError(self.token_list.prev(), "Expected argument after unary operation, not binary operator.").throw()
            elif tok.type == tb.SyntaxToken.label:
                return ret_operation(self.context_label_trunk(tok.value, templates))
            elif tok.type == tb.SyntaxToken.parentheses_start:
                return ret_operation(self.context_order_of_operations(templates)[0])
    
    def context_index(self, beginning:Operation, templates:list[str], dereferences = 0):
        "This is for the `[index]` operator."
        indexes = [beginning]
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.delimiter:
                continue
            elif tok.type == tb.SyntaxToken.sqr_bracket_end:
                continue
            elif tok.type == tb.SyntaxToken.sqr_bracket_start:
                continue
            elif tok.type == tb.SyntaxToken.access_op:
                return self.context_access(IndexOperation(indexes, token=self.token_list.prev()), templates, dereferences)
            elif tok.type == tb.SyntaxToken.dereference_access_op:
                return self.context_access(DereferenceOperation([IndexOperation(indexes, token=self.token_list.prev())], token=self.token_list.prev()), templates, dereferences)
            elif tok.type.is_ending_token or tok.type.is_lhs_rhs_operator:
                self.token_list.prepend(tok)
                break
            else:
                self.token_list.prepend(tok)
                ooo_res = self.context_order_of_operations(templates)
                indexes.append(ooo_res[0])
                if ooo_res[1].type != tb.SyntaxToken.delimiter and ooo_res[1].type.is_ending_token:
                    break
        
        return IndexOperation(indexes, token=self.token_list.prev())
    
    def context_access(self, beginning:Operation, templates:list[str], dereferences = 0):
        "This is for the `.` operator."
        indexes = [beginning]
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.access_op:
                continue
            elif tok.type == tb.SyntaxToken.dereference_access_op:
                indexes = [DereferenceOperation([AccessOperation(indexes, token=self.token_list.prev())], token=self.token_list.prev())]
            elif tok.type == tb.SyntaxToken.sqr_bracket_start:
                return self.context_index(DereferenceOperation([AccessOperation(indexes, token=self.token_list.prev())], token=self.token_list.prev()), templates, dereferences)
            elif tok.type == tb.SyntaxToken.address_op:
                return self.context_index(AddressOperation([AccessOperation(indexes, token=self.token_list.prev())], token=self.token_list.prev()), templates, dereferences)
            elif tok.type == tb.SyntaxToken.label:
                indexes.append(LookupLabel(tok.value))
            elif tok.type == tb.SyntaxToken.macro_delimiter_op:
                self.token_list.prepend(tok)
                indexes = [self.context_call(AccessOperation(indexes, token=self.token_list.prev()), templates, dereferences)]
            elif tok.type == tb.SyntaxToken.parentheses_start:
                self.token_list.prepend(tok)
                indexes = [self.context_call(AccessOperation(indexes, token=self.token_list.prev()), templates, dereferences)]
            else:
                self.token_list.prepend(tok)
                break
        #print(indexes)
        if len(indexes) == 1:
            if isinstance(indexes[0], CallOperation):
                return indexes[0]
        return AccessOperation(indexes, token=self.token_list.prev())
    
    def context_call(self, function:Operation | str, templates:list[str], dereferences = 0):
        "This is for the `label?<templates...>(args...)` operator."
        #print(f"\n\nCONTEXT_CALL {self.token_list.current()}\n")
        is_template_function = self.token_list.current().type == tb.SyntaxToken.macro_delimiter_op
        
        template_args = []
        if is_template_function:
            next(self.token_list) # skip the ? token
            for tok in self.token_list:
                
                match tok.type:
                    case tb.SyntaxToken.less_than_op:
                        template_args = self.context_template(templates)
                        break
                    case _:
                        ce.CompilerError(tok,
                            "Expected template type arguments in call following `?` token.",
                            hint="example: func_name?<i32>(argument);"
                        ).throw()
        function_args = []
        #print(f"FUNC ARGS STARTING TOK {self.token_list.current()}")
        if self.token_list.current().type == tb.SyntaxToken.parentheses_start:
            next(self.token_list) # skip the ( token
        
        for tok in self.token_list:
            #print(f"Call ARG token: {tok}")
            if tok.type == tb.SyntaxToken.delimiter:
                continue
            elif tok.type == tb.SyntaxToken.parentheses_end:
                break
            else:
                self.token_list.prepend(tok)
                #self.dbg_print(f"FA TOK {self.token_list.current()} : {function}")
                ooo_ret = self.context_order_of_operations(templates)
                if ooo_ret[0] != None:
                    function_args.append(ooo_ret[0])
                if ooo_ret[1] != None:
                    if ooo_ret[1].type == tb.SyntaxToken.parentheses_end:
                        break

        #print(f"END CALL")
        
        #print(f"\nF CLOSE {function}")
        
        return CallOperation(function, function_args, template_args, token=self.token_list.prev())

    def context_label_trunk(self, label:str, templates:list[str], dereferences = 0):
        ret_val = label
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.macro_delimiter_op:
                # is a template function
                self.token_list.prepend(tok)
                self.dbg_print(f"TF {ret_val}, {templates}, {dereferences}")
                ret_val = self.context_call(ret_val, templates, dereferences)
                
            elif tok.type == tb.SyntaxToken.parentheses_start:
                # is a function that may be a template function
                self.token_list.prepend(tok)
                self.dbg_print(f"F  {ret_val}, {templates}, {dereferences}")
                ret_val = self.context_call(ret_val, templates, dereferences)
            elif tok.type == tb.SyntaxToken.access_op:
                ret_val = self.context_access(ret_val, templates, dereferences)
            elif tok.type == tb.SyntaxToken.dereference_access_op:
                ret_val = self.context_access(DereferenceOperation([ret_val], token=self.token_list.prev()), templates, dereferences)
            elif tok.type == tb.SyntaxToken.sqr_bracket_start:
                ret_val = self.context_index(DereferenceOperation([ret_val], token=self.token_list.prev()), templates, dereferences)
            elif tok.type == tb.SyntaxToken.address_op:
                ret_val = self.context_index(AddressOperation([ret_val], token=self.token_list.prev()), templates, dereferences)
            else:
                if tok.type == tb.SyntaxToken.assign_op:
                    
                    ooo_ret = self.context_order_of_operations(templates)
                    #self.dbg_print(f"ASSIGN OP {[ret_val, ooo_ret[0]]}")
                    self.token_list.prepend(ooo_ret[1])
                    return AssignOperation([prepend_derefs(ret_val, dereferences), ooo_ret[0]], token=self.token_list.prev())
                else:
                    self.token_list.prepend(tok)
                return prepend_derefs(ret_val, dereferences)
                


    def context_define(self, templates:list[str]):
        """
        This is the context trunk for the left hand side of an assignment operator.

        NOTE: This is used for `let` statements.
        """
        name = ""
        typ = None
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.label:
                name = tok.value
            elif tok.type == tb.SyntaxToken.cast_op:
                typ = self.context_type_trunk(templates)

            elif tok.type == tb.SyntaxToken.assign_op:
                ooo_ret = self.context_order_of_operations(templates)
                #print([name, ooo_ret[0]])
                
                return DefineOperation([name, ooo_ret[0]], force_type=typ, token=self.token_list.prev())

            elif tok.type.is_ending_token:
                # if there is no assignment operator, then the line_end token will
                # not be consumed and this block will execute.
                # This allocates a variable without assigning a value.
                
                return DefineOperation([name, Value(typ)], token=self.token_list.prev())

    def context_conditional_statement(self, statement_type: tb.SyntaxToken, templates:list[str]):
        
        condition = None
        scope = []
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.let_keyword:
                    condition = self.context_define(templates)
                case tb.SyntaxToken.scope_start:
                    #print(condition)
                    scope = self.context_scope_trunk(templates)
                    break
                case _:
                    self.token_list.prepend(tok)
                    
                    oop_ret = self.context_order_of_operations(templates)
                    condition =  oop_ret[0]
                    if oop_ret[1].type == tb.SyntaxToken.scope_start:
                        scope = self.context_scope_trunk(templates)
                        break
        
        match statement_type:
            case tb.SyntaxToken.if_keyword:
                return IfBlock(condition=[condition], scope=scope)
            case tb.SyntaxToken.elif_keyword:
                return ElseIfBlock(condition=[condition], scope=scope)
            case tb.SyntaxToken.else_keyword:
                return ElseBlock(scope=scope)
            case tb.SyntaxToken.while_keyword:
                return WhileLoop(condition=[condition], scope=scope)
                
    
    def context_scope_trunk(self, templates:list[str], documentation = None):
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
                    let = self.context_define(templates)
                    #print(let)
                    scope.append(let)

                case tb.SyntaxToken.if_keyword | tb.SyntaxToken.elif_keyword | tb.SyntaxToken.else_keyword | tb.SyntaxToken.while_keyword:
                    self.dbg_scope_padding += 1
                    scope.append(self.context_conditional_statement(tok.type, templates))
                    self.dbg_scope_padding -= 1

                case tb.SyntaxToken.label:
                    l=self.context_label_trunk(tok.value, templates, deref)
                    #print(l)
                    scope.append(l)
                    deref = 0
                case tb.SyntaxToken.parentheses_start:
                    scope.append(self.context_label_trunk((self.context_order_of_operations(templates)[0]), templates, deref))
                    deref = 0
                case tb.SyntaxToken.return_op:
                    ret_val = self.context_order_of_operations(templates)
                    if ret_val[0] == None:
                        scope.append(FunctionReturnOperation(token=self.token_list.prev()))
                    else:
                        scope.append(FunctionReturnOperation([ret_val[0]], token=self.token_list.prev()))
                case tb.SyntaxToken.break_op:
                    scope.append(BreakOperation(token=self.token_list.prev()))
                    #skip the ; token
                    next(self.token_list)
                case tb.SyntaxToken.string_literal:
                    documentation["purpose"] = tok.value
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

    def context_function_statement_definition(self, templates:list[str], extern = False, virtual = False):
        """
        This defines the statement part of the function.
        
        The scope of the function is handled by context_scope.
        """
        name = ""
        template_definition:list[str] = []
        scope = []
        return_type:CompilerType = VoidType()
        arguments:dict[str,CompilerType] = {}
        documentation = {"purpose":None,"implementation": None,"args": {}}
        for tok in self.token_list:
            if (tok.type.is_lhs_rhs_operator or tok.type.is_single_arg_operator) and not tok.type in {tb.SyntaxToken.less_than_op, tb.SyntaxToken.greater_than_op}:
                name += tok.value
                #print(name)
            else:
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
                        scope = self.context_scope_trunk([*templates, *template_definition], documentation)
                        #print(name)
                        #print(scope)
                        break
        
        #print(f"{'extern ' if extern else ''}func {name}<{template_definition}>({arguments}) ~> {return_type} {{{scope}}}")
        #print("\n".join([repr(line) for line in scope]))
        return FunctionDefinition(name, arguments, return_type, False, template_definition, scope, extern=extern, documentation=documentation, virtual=virtual)
    
    def context_struct_definition(self):
        name = ""
        attributes = {}
        functions = []
        operators = []
        templates:list[str] = []
        documentation = {"purpose":""}

        # first parse the statement before the curly brackets to add struct
        # to the namespace and get the struct template names

        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    name = tok.value
                case tb.SyntaxToken.less_than_op:
                    templates = self.context_template_definition()
                    break
                case tb.SyntaxToken.scope_start:
                    break
                
        
        #print(name)
        self.struct_namespace.append(StructOption(name, templates))
        
        # then parse the definition of the struct within the curly braces
        virtual = False
        attribute_label_buffer = ""
        for tok in self.token_list:
            match tok.type:
                case tb.SyntaxToken.label:
                    attribute_label_buffer = tok.value
                case tb.SyntaxToken.cast_op:
                    attributes[attribute_label_buffer] = self.context_type_trunk(templates)
                    attribute_label_buffer = ""
                case tb.SyntaxToken.virtual_keyword:
                    virtual = True
                case tb.SyntaxToken.func_keyword:
                    mf = self.context_function_statement_definition(templates, virtual=virtual)
                    functions.append(mf)
                    virtual = False
                case tb.SyntaxToken.operator_func_keyword:
                    omf = self.context_function_statement_definition(templates, virtual=virtual)
                    for a_t in omf.arguments.values():
                        omf.name += f"_arg_{a_t.name}"
                    operators.append(omf)
                    virtual = False
                case tb.SyntaxToken.scope_end:
                    break
                case tb.SyntaxToken.string_literal:
                    documentation["purpose"] = tok.value
        
        return StructDefinition(name, attributes, functions, templates, documentation=documentation, operatorfunctions=operators)


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
            elif not tok.type == tb.SyntaxToken.delimiter:
                type_templates.append(self.get_type(tok, templates, pointer))
                pointer = 0
        
        return type_templates

    def context_type_struct(self, name:str, templates:list[str], pointer = 0) -> CompilerType:
        """
        The type hint context for structs.
        """
        struct_option:StructOption = None
        for struct in self.struct_namespace:
            if name == struct:
                struct_option = struct

        if not struct_option.has_templates:
            if pointer > 0:
                return StructType(name, ptr_count=pointer)
            else:
                return StructType(name)
        
        for tok in self.token_list:
            if tok.type == tb.SyntaxToken.less_than_op:
                temps = self.context_template(templates)
                if pointer > 0:
                    return StructType(name, temps, ptr_count=pointer)
                else:
                    return StructType(name, temps)
            else:
                if tok.type == tb.SyntaxToken.greater_than_op:
                    self.token_list.prepend(tok)
                if pointer > 0:
                    return StructType(name, ptr_count=pointer)
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
                l = self.context_type_list(templates)
                #print(self.token_list)
                return get_ptr(l)
            
            case tb.SyntaxToken.label:
                if tok.value in self.struct_namespace:
                    struc = self.context_type_struct(tok.value, templates, pointer)
                    #print(struc)
                    return struc
                elif tok.value in templates:
                    if pointer > 0:
                        return Template(tok.value, ptr_count=pointer)
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
                return get_ptr(BoolType())
            
            case tb.SyntaxToken.c8_type:
                return get_ptr(C8Type())
            


def prepend_derefs(instr, derefs:int):
    ret_ins = instr
    for _ in range(derefs):
        ret_ins = DereferenceOperation([ret_ins])

    return ret_ins