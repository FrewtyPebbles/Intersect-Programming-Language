import sys
from llvmcompiler.compiler_tokenizer.tokenizer import Tokenizer

class CLI:
    def __init__(self) -> None:
        self.arguments:dict[str,str|bool] = {
            "debug":False,
            "source":"./main.pop",
            "output":"./program"
        }
        flag = ""
        for raw_argument in sys.argv:
            argument = raw_argument.lower()
            if argument in {"-output", "-o"}:
                flag = argument
            elif argument in {"-source", "-s"}:
                flag = argument
            elif argument in {"-debug", "-dbg", "-d"}:
                self.arguments["debug"] = True
            elif flag in {"-output", "-o"}:
                self.arguments["output"] = argument
                flag = ""
            elif flag in {"-source", "-s"}:
                self.arguments["source"] = argument
                flag = ""
        
        with open(self.arguments["source"], "r") as file:
            src = file.read()
            self.tokenizer = Tokenizer(src, self.arguments["output"])

    def run(self):
        token_list = self.tokenizer.tokenize()
        for token in token_list:
            sys.stdout.write(f"{token.value} ||||| {token.type.name}\n")
