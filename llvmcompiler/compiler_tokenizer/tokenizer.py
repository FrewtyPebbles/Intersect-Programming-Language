from llvmcompiler.compiler_tokenizer.utility import regex_in
from .token import SyntaxToken, Token


#                                     .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
#                                     | This Tokenizer uses Parsing Contexts! |
#                                     '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~\
# How Parsing Contexts Works  \___________________________________________________________________________________________
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~V                                                                                          |
#                                                                                                                         |
#   In the main tokenizer function there are a bunch of conditions/edge cases to identify the starts of parsing contexts. |
#                                                                                                                         |
#       Parsing contexts read characters into a string buffer until they reach certain characters/edge cases.             |
#_________________________________________________________________________________________________________________________|
#                                                                                                                         |
#  TODO: Parsing Contexts to make:                                                                                        |
#                                                                                                                         |
#    - A string parsing context. [WIP]                                                                                    |
#                                                                                                                         |
#    - An operator parsing context. [Not Started]                                                                         |
#                                                                                                                         |
#    - A label/keyword parsing context. [Needs Refactoring so as not to interfere with number parsing.]                   |
#                                                                                                                         |
#    - A number parsing context. [Not Started]                                                                            |
#_________________________________________________________________________________________________________________________|

class Tokenizer:
    def __init__(self, src:str, output = "") -> None:
        self.src = get_str_itterator(src)
        self.output = output
        self.token_list:list[Token] = []

    def tokenize(self):
        # this is where the code gets tokenized
        self.keyword = ""
        last_char = ""
        for char in self.src:
            match regex_in(char):
                case r"\"":
                    self.parse_keystring()
                    self.parse_string(char)
                    last_char = char
                    continue
                case r"\'":
                    self.parse_keystring()
                    self.parse_string(char)
                    last_char = char
                    continue
                case r"[{]":
                    self.parse_keystring_and_append_token(SyntaxToken.scope_start)
                    last_char = char
                    continue
                case r"[}]":
                    self.parse_keystring_and_append_token(SyntaxToken.scope_end)
                    last_char = char
                    continue
                case r"[(]":
                    self.parse_keystring_and_append_token(SyntaxToken.parentheses_start)
                    last_char = char
                    continue
                case r"[)]":
                    self.parse_keystring_and_append_token(SyntaxToken.parentheses_end)
                    last_char = char
                    continue
                case r"[:]":
                    self.parse_keystring_and_append_token(SyntaxToken.specifier_op)
                    last_char = char
                    continue
                case r"[:]":
                    self.parse_keystring_and_append_token(SyntaxToken.specifier_op)
                    last_char = char
                    continue
                case r"[;]":
                    self.parse_keystring_and_append_token(SyntaxToken.line_end)
                    last_char = char
                    continue
                case r"[,]":
                    self.parse_keystring_and_append_token(SyntaxToken.delimiter)
                    last_char = char
                    continue
                case r"[[]":
                    self.parse_keystring_and_append_token(SyntaxToken.array_start)
                    last_char = char
                    continue
                case r"[]]":
                    self.parse_keystring_and_append_token(SyntaxToken.array_end)
                    last_char = char
                    continue
                case r"[+]":
                    self.parse_keystring_and_append_token(SyntaxToken.add_op)
                    last_char = char
                    continue
                case r"[-]":
                    self.parse_keystring_and_append_token(SyntaxToken.subtract_op)
                    last_char = char
                    continue
                case r"[*]":
                    self.parse_keystring_and_append_token(SyntaxToken.multiply_op)
                    last_char = char
                    continue
                case r"[$]":
                    self.parse_keystring_and_append_token(SyntaxToken.dereference_op)
                    last_char = char
                    continue
                case r"[/]":
                    self.parse_keystring_and_append_token(SyntaxToken.divide_op)
                    last_char = char
                    continue
                case r"[.]":
                    if not last_char.isnumeric():
                        self.parse_keystring_and_append_token(SyntaxToken.access_op)
                    else:
                        self.keyword += char
                    last_char = char
                    continue
                case r"[#]":
                    self.parse_keystring()
                    self.parse_comment()
                    continue
                case r"[=~<>]":
                    
                    if regex_in(last_char) == r"[=~<>]":
                        if not last_char in {"~"}:
                            self.token_list.pop()
                        self.append_token_only(SyntaxToken(last_char + char))
                    elif char != "~":
                        self.parse_keystring_and_append_token(SyntaxToken(char))
                    last_char = char
                    continue
                case r"[\s\n\t]":
                    self.parse_keystring()
                    last_char = char
                    continue
                case _:
                    if not last_char.isalnum() and last_char != "_":
                        self.parse_keystring()
                    self.keyword += char
                    last_char = char
                    continue
            
                     

        return self.token_list

    
    def previous_is(self, token:SyntaxToken):
        return self.token_list[len(self.token_list)-1].value == token
    
    def parse_keystring_and_append_token(self, token:SyntaxToken):
        self.parse_keystring()
        self.append_token_only(token)

    def parse_keystring(self):
        """
        This parsing context parses keyword into the correct syntax token type.
        """
        if self.keyword in {e.value for e in SyntaxToken}:
            self.append_token_only(SyntaxToken(self.keyword))
        elif self.keyword == "":
            pass
        elif self.keyword in {"true", "false"}:
            self.append_token(SyntaxToken.bool_literal, self.keyword)
        elif self.keyword.strip(".").isnumeric():
            self.parse_literal()
        else:
            self.append_token(SyntaxToken.label, self.keyword)

        self.keyword = ""

    def parse_literal(self):
        self.token_list.append(Token.new(self.keyword))

    def parse_string(self, tok:str):
        escape = False
        string = ""
        for char in self.src:
            if not escape:
                if char == tok:
                    self.append_token(SyntaxToken.string_literal, string + "\0")
                    return
                string += char
            
            else:
                match char:
                    case "n":
                        pass
    
    def parse_comment(self):
        for char in self.src:
            if char == "\n":
                return
                
    def append_token(self, token:SyntaxToken, value = ""):
        self.token_list.append(Token(value, token))

    def append_token_only(self, token:SyntaxToken):
        self.token_list.append(Token(token.value, token))

    
def get_str_itterator(string:str):
    for char in string:
        yield char