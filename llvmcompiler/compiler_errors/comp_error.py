from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import llvmcompiler.tree_builder.token as tb

class Color:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

class CompilerError:
    def __init__(self, token, msg:str, hint:str = None) -> None:
        self.token:tb.Token = token
        self.column_number = self.token.column_number
        self.line_number = self.token.line_number
        self.file = self.token.file
        self.msg = msg
        self.line = self.token.line
        self.prev_line = self.token.prev_line
        self.next_line = self.token.next_line
        self.hint = hint

    def __repr__(self):
        def_col = Color.LIGHT_WHITE
        bord_col = Color.LIGHT_WHITE
        num_color = f"{Color.LIGHT_WHITE}"
        firstline = f"\n{bord_col}┈┄─{Color.RED}ERROR {def_col}[ {Color.YELLOW}File {def_col}\"{self.file}\", {Color.YELLOW}Line {num_color}{self.line_number}{def_col}, {Color.YELLOW}Column {num_color}{self.column_number} {def_col}]{bord_col}─┄┈\n"
        l_slice_ind = (self.column_number - 1 - len(str(self.token.value)))
        self.line = self.line[:l_slice_ind] + Color.UNDERLINE + self.line[l_slice_ind:l_slice_ind+(len(str(self.token.value)))]+ Color.END + self.line[l_slice_ind + len(str(self.token.value)):]
        return (
            firstline +
            f"{bord_col}╭────┄┈{Color.RED} {self.msg}\n" +
            (f"{bord_col}│{num_color}{self.line_number-1}{bord_col}┊{def_col}{Color.FAINT}{self.prev_line}{Color.END}\n" if self.prev_line != None else "") + 
            f"{bord_col}│{num_color}{self.line_number}{bord_col}│{def_col}{self.line}\n" +
            (f"{bord_col}│{num_color}{' ' * len(str(self.line_number+1))}{bord_col}│{def_col}{' ' * (self.column_number - 1 - len(str(self.token.value)))}{' ' * (len(str(self.token.value))-1)}╰─ {self.hint}\n" if self.hint != None else "") +
            (f"{bord_col}│{num_color}{self.line_number+1}{bord_col}┊{def_col}{Color.FAINT}{self.next_line}{Color.END}\n" if self.next_line != None else "") +
            f"{bord_col}└─┄┈\n{Color.END}"
        )
    
    def throw(self):
        print(self)
        exit()