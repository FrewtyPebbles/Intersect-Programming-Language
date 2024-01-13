

class CompilerError:
    def __init__(self, cn:int = None, ln:int = None, file = "unknown", msg = "Unknown error.") -> None:
        self.column_number = cn
        self.line_number = ln
        self.file = file
        self.msg = msg

    def __repr__(self):
        firstline = f"\n ERROR [ File \"{self.file}\", Line {self.line_number}, Column {self.column_number} ]:\n"
        return (
            firstline +
            f"\t{self.msg}\n"
        )
    
    def throw(self):
        print(self)
        exit()