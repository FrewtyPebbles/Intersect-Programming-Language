import sys
from llvmcompiler.tree_builder import Tokenizer, SyntaxToken, TreeBuilder

class CLI:
    def __init__(self) -> None:
        self.arguments:dict[str,str|bool] = {
            "debug":False,
            "source":"./main.pop",
            "output":"./program",
            "salt": "MMAANNGGLLEE"
        }
        flag = ""
        for raw_argument in sys.argv:
            argument = raw_argument.lower()
            if argument in {"-output", "-o"}:
                flag = argument
            elif argument in {"-source", "-s"}:
                flag = argument
            elif argument in {"-salt", "-sal", "-mangle", "-mang"}:
                flag = argument
            elif argument in {"-debug", "-dbg", "-d"}:
                self.arguments["debug"] = True
            elif flag in {"-output", "-o"}:
                self.arguments["output"] = argument
                flag = ""
            elif flag in {"-source", "-s"}:
                self.arguments["source"] = argument
                flag = ""
            elif flag in {"-salt", "-sal", "-mangle", "-mang"}:
                self.arguments["salt"] = argument
                flag = ""
        
        with open(self.arguments["source"], "r") as file:
            src = file.read()
            self.tokenizer = Tokenizer(src, self.arguments["output"])

    def run(self):
        token_list = self.tokenizer.tokenize()
        
        tree = TreeBuilder(token_list, self.arguments["source"], self.arguments["salt"])

        # for token in token_list:
        #     tw = ""
        #     if token.type == SyntaxToken.string_literal:
        #         tw = "\""
        #     sys.stdout.write(f"{tw}{token.value}{tw}{' ' * (30 - len(str(token.value)))}{token.type.name}\n")

        tree.parse_trunk()


        module = tree.get_module()

        module.write()

        module.dbg_print()

        
