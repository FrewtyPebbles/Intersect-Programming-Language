from enum import Enum

class SyntaxToken(Enum):
    scope_start = "{"
    scope_end = "}"
    if_keyword = "if"
    elif_keyword = "elif"
    else_keyword = "else"
    func_keyword = "func"
    operator_func_keyword = "OPERATOR"
    for_keyword = "for"
    let_keyword = "let"
    heap_keyword = "heap"
    fn_specifier_op = "~>"
    add_op = "+"
    subtract_op = "-"
    multiply_op = "*"
    divide_op = "/"
    modulo_op = "%"
    dereference_op = "$"
    less_than_op = "<"
    greater_than_op = ">"
    equal_to_op = "=="
    not_equal_to_op = "!="
    not_op = "!"
    and_op = "and"
    or_op = "or"
    less_than_or_equal_to_op = "<="
    greater_than_or_equal_to_op = ">="
    parentheses_start = "("
    parentheses_end = ")"
    string_literal = "string"
    integer_literal = "integer"
    precision_literal = "precision"
    bool_literal = "boolean"
    null_literal = "null"
    i64_type = "i64"
    i32_type = "i32"
    i8_type = "i8"
    c8_type = "c8"
    f32_type = "f32"
    d64_type = "d64"
    bool_type = "bool"
    str_type = "str"
    label = "label"
    sqr_bracket_start = "["
    sqr_bracket_end = "]"
    comment_start = "#:"
    comment_end = ":#"
    assign_op = "="
    delimiter = ","
    cast_op = ":"
    line_end = ";"
    return_op = "return"
    access_op = "."
    post_increment_op = "++"
    post_decrement_op = "--"
    struct_keyword = "struct"
    error_keyword = "ERROR"
    persist_keyword = "persist"
    delete_keyword = "delete"
    export_keyword = "export" # this is the same as extern "c"

    @property
    def priority(self):
        #PEMDAS
        match self:
            case SyntaxToken.scope_start:
                return 1
            case SyntaxToken.scope_end:
                return 1
            case SyntaxToken.parentheses_start:
                return 1
            case SyntaxToken.parentheses_end:
                return 1
            case SyntaxToken.sqr_bracket_start:
                return 1
            case SyntaxToken.sqr_bracket_end:
                return 1
            case SyntaxToken.access_op:
                return 2
            case SyntaxToken.dereference_op:
                return 2
            case SyntaxToken.heap_keyword:
                return 2
            case SyntaxToken.cast_op:
                return 2
            case SyntaxToken.divide_op:
                return 3
            case SyntaxToken.multiply_op:
                return 3
            case SyntaxToken.modulo_op:
                return 3
            case SyntaxToken.add_op:
                return 4
            case SyntaxToken.subtract_op:
                return 4
            case SyntaxToken.greater_than_op:
                return 5
            case SyntaxToken.less_than_op:
                return 5
            case SyntaxToken.greater_than_or_equal_to_op:
                return 5
            case SyntaxToken.less_than_or_equal_to_op:
                return 5
            case SyntaxToken.not_equal_to_op:
                return 6
            case SyntaxToken.equal_to_op:
                return 6
            case SyntaxToken.and_op:
                return 7
            case SyntaxToken.or_op:
                return 7
            case SyntaxToken.assign_op:
                return 8
            case SyntaxToken.delimiter:
                return 9
            
        return 999

    

class Token:
    value:any
    type:SyntaxToken
    def __init__(self, value:str = None, syntax_type:SyntaxToken = None) -> None:
        self.value = value
        self.type = syntax_type

    @property
    def priority(self):
        """
        The priority of the current token's operator.

        If the token is not an operator and does not have a priority,
        its priority will be 999.
        """
        return self.type.priority

    @staticmethod
    def new(value:str = None, syntax_type:SyntaxToken = None):
        if value != None and syntax_type != None:
            return Token(value, syntax_type)
        elif value == "true" or value == "false":# bool
            if value == "true":
                return Token(True, SyntaxToken.bool_literal)
            elif value == "false":
                return Token(False, SyntaxToken.bool_literal)
        elif value.isdecimal():# u32
            return Token(int(value), SyntaxToken.integer_literal)
        elif value.startswith("-") and value.lstrip("-").lstrip().isdecimal():# i32
            return Token(int(value), SyntaxToken.integer_literal)
        elif "." in value and value.replace(".", "").lstrip("-").isdecimal():# f32
            return Token(float(value), SyntaxToken.precision_literal)
        else:
            print("Error: Unable to determine type of token.")

    def __repr__(self) -> str:
        return f"\n{{Token:[type:{self.type}|value:{self.value}]}}"