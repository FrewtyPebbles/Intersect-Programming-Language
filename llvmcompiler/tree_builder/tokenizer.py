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
    def __init__(self, src:str, output = "", file_name = "unknown") -> None:
        self.src = get_str_itterator(src)
        self.output = output
        self.token_list:list[Token] = []
        self.line_num = 1
        self.column_num = 0
        self.file_name = file_name
        self.lines = ["", *src.splitlines()]

    def inc_c(self, char:str):
        "increment the column number"
        if char in {'\n','\r'}:
            self.column_num = 0
            self.line_num += 1
        else:
            self.column_num += 1

    def tokenize(self):
        # this is where the code gets tokenized
        self.keyword = ""
        for char in self.src:
            self.inc_c(char)
            self.parse_char(char)

        return self.token_list
    
    def parse_char(self, char:str):
        match regex_in(char):
            case r"[{}():;,\[\]$&.]":
                
                self.parse_keystring_and_append_token(SyntaxToken(char))
                
                return
            case r"[!~<>=*\-/+\?%]":
                
                self.keyword += char
                self.operator_context()
                return
            
                
            case r"[0-9.]":
                self.keyword += char
                self.number_context()
                return
                
            case r"[A-Za-z_]":
                self.keyword += char
                self.label_context()
                return
            case r"[\"\']":
                self.string_context(char)
                return
            case r"\s":
                return
            case r"[#]":
                self.comment_context()
                return
            case _:
                
                return

    def string_context(self, tok:str):
        self.parse_keystring()
        escape = False
        string = ""
        for char in self.src:
            self.inc_c(char)
            if not escape:
                if char == "\\":
                    escape = True
                    continue
                if char == tok:
                    if tok == "'":
                        self.append_token(SyntaxToken.integer_literal, ord(string))
                    else:
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
            self.inc_c(char)
            if regex_in(char) == r"[~<>=\*-/+_]":
                self.keyword += char
            else:
                self.parse_keystring()
                self.parse_char(char)
                return

    def label_context(self):
        for char in self.src:
            self.inc_c(char)
            if regex_in(char) == r"[A-Za-z0-9_]":
                self.keyword += char
            else:
                self.parse_keystring()
                self.parse_char(char)
                return
    
    def number_context(self):
        for char in self.src:
            self.inc_c(char)
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
        multiline = False
        last_char = ""
        for c_n, char in enumerate(self.src):
            self.inc_c(char)
            if (char == "\n" and not multiline) or last_char + char == ":#":
                return
            elif char == ":" and c_n == 0:
                multiline = True
            last_char = char
    
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
        elif self.keyword == ">,":
            self.append_token_only(SyntaxToken(">"))
            self.append_token_only(SyntaxToken(","))
        elif self.keyword == ">"*len(self.keyword):
            for _ in range(len(self.keyword)):
                self.append_token_only(SyntaxToken(">"))
        elif self.keyword == "?<":
            self.append_token_only(SyntaxToken("?"))
            self.append_token_only(SyntaxToken("<"))
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
        # Get prev and next line
        prev_line = None
        if self.line_num > 1:
            prev_line=self.lines[self.line_num-1]
        next_line = None
        if len(self.lines) > self.line_num + 1:
            next_line=self.lines[self.line_num+1]

        # append to token list
        self.token_list.append(Token.new(self.keyword, cn=self.column_num, ln=self.line_num, file=self.file_name, line=self.lines[self.line_num], prev_line=prev_line, next_line=next_line))

                
    def append_token(self, token:SyntaxToken, value = ""):
        # Get prev and next line
        prev_line = None
        if self.line_num > 1:
            prev_line=self.lines[self.line_num-1]
        next_line = None
        if len(self.lines) > self.line_num + 1:
            next_line=self.lines[self.line_num+1]

        # append to token list
        self.token_list.append(Token(value, token, self.column_num, self.line_num, self.file_name, self.lines[self.line_num], prev_line=prev_line, next_line=next_line))

    def append_token_only(self, token:SyntaxToken):
        # Get prev and next line
        prev_line = None
        if self.line_num > 1:
            prev_line=self.lines[self.line_num-1]
        next_line = None
        if len(self.lines) > self.line_num + 1:
            next_line=self.lines[self.line_num+1]

        # append to token list
        self.token_list.append(Token(token.value, token, self.column_num, self.line_num, self.file_name, self.lines[self.line_num], prev_line=prev_line, next_line=next_line))

    
def get_str_itterator(string:str):
    for char in string:
        yield char