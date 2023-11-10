from enum import Enum

class SyntaxToken(Enum):
    scope_start = "{"
    scope_end = "}"
    if_keyword = "if"
    elif_keyword = "elif"
    else_keyword = "else"
    fn_keyword = "fn"
    for_keyword = "for"
    let_keyword = "let"
    heap_keyword = "heap"
    fn_specifier_op = "~>"
    add_op = "+"
    subtract_op = "-"
    multiply_op = "*"
    divide_op = "/"
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
    i32_type = "i32"
    i8_type = "i8"
    c8_type = "c8"
    f32_type = "f32"
    d64_type = "d64"
    bool_type = "bool"
    str_type = "str"
    label = "label"
    array_start = "["
    array_end = "]"
    comment_start = "#:"
    comment_end = ":#"
    assign_op = "="
    delimiter = ","
    specifier_op = ":"
    line_end = ";"
    return_op = "return"
    access_op = "."
    post_increment_op = "++"
    post_decrement_op = "--"
    struct_keyword = "struct"
    

class Token:
    value:any
    type:SyntaxToken
    def __init__(self, value:str = None, syntax_type:SyntaxToken = None) -> None:
        self.value = value
        self.type = syntax_type

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