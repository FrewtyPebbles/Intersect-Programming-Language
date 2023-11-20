from llvmcompiler.tree_builder.utility import regex_in
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
#    - An operator parsing context. [Done]                                                                                |
#                                                                                                                         |
#    - A label/keyword parsing context. [Done]                                                                            |
#                                                                                                                         |
#    - A number parsing context. [Done]                                                                                   |
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
            self.parse_char(char)

        return self.token_list
    
    def parse_char(self, char:str):
        match regex_in(char):
            case r"[{}():;,\[\]$.]":
                self.parse_keystring_and_append_token(SyntaxToken(char))
                last_char = char
                return
            case r"[~<>=*\-/+]":
                self.keyword += char
                self.operator_context()
                last_char = char
                return
                
            case r"[0-9.]":
                self.keyword += char
                self.number_context()
                last_char = char
                return
                
            case r"[A-Za-z_]":
                self.keyword += char
                self.label_context()
                last_char = char
                return
            case r"[\"\']":
                self.string_context(char)
                last_char = char
                return
            case r"\s":
                return
            case r"[#]":
                self.comment_context()
                return
            case _:
                # if not last_char.isalnum() and last_char != "_":
                #     self.parse_keystring()
                # self.keyword += char
                last_char = char
                return

    def string_context(self, tok:str):
        self.parse_keystring()
        escape = False
        string = ""
        for char in self.src:
            if not escape:
                if char == "\\":
                    escape = True
                    continue
                if char == tok:
                    print(string)
                    self.append_token(SyntaxToken.string_literal, string + "\0")
                    return
                string += char
            
            else:
                match char:
                    case "n":
                        string += "\n"
                    case "\\":
                        string += "\\"
                    case "0":
                        string += "\00"
                    case "t":
                        string += "\t"
                    case "r":
                        string += "\r"
                escape = False

    def operator_context(self):
        for char in self.src:
            if regex_in(char) == r"[~<>=*-/+_]":
                self.keyword += char
            else:
                self.parse_keystring()
                self.parse_char(char)
                return

    def label_context(self):
        for char in self.src:
            if regex_in(char) == r"[A-Za-z0-9_]":
                self.keyword += char
            else:
                self.parse_keystring()
                self.parse_char(char)
                return
    
    def number_context(self):
        for char in self.src:
            if regex_in(char) == r"[0-9.]":
                self.keyword += char
            else:
                if "." in self.keyword:
                    self.append_token(SyntaxToken.precision_literal, float(self.keyword))
                else:
                    self.append_token(SyntaxToken.integer_literal, int(self.keyword))
                self.keyword = ""
                self.parse_char(char)
                return

    
    def comment_context(self):
        self.parse_keystring()
        for char in self.src:
            if char == "\n":
                return
    
    def previous_is(self, token:SyntaxToken):
        return self.token_list[len(self.token_list)-1].value == token
    
    def parse_keystring_and_append_token(self, token:SyntaxToken):
        self.parse_keystring()
        self.append_token_only(token)

    def parse_keystring(self):
        """
        This parsing context parses keyword into the correct syntax token type.
        """
        if self.keyword == "":
            return
        elif self.keyword in {e.value for e in SyntaxToken}:
            self.append_token_only(SyntaxToken(self.keyword))
        elif self.keyword in {"true", "false"}:
            self.append_token(SyntaxToken.bool_literal, self.keyword)
        elif self.keyword.strip(".").isnumeric():
            self.parse_literal()
        else:
            self.append_token(SyntaxToken.label, self.keyword)

        self.keyword = ""

    def parse_literal(self):
        self.token_list.append(Token.new(self.keyword))

                
    def append_token(self, token:SyntaxToken, value = ""):
        self.token_list.append(Token(value, token))

    def append_token_only(self, token:SyntaxToken):
        self.token_list.append(Token(token.value, token))

    
def get_str_itterator(string:str):
    for char in string:
        yield char