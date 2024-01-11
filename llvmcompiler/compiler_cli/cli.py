import os
import platform
import subprocess
import sys
from llvmcompiler.tree_builder import Tokenizer, SyntaxToken, TreeBuilder

VERSION = "0.1.0"

class CLI:
    
    def __init__(self) -> None:
        self.arguments:dict[str,str|bool] = {
            "debug":False,
            "source": None,
            "output": None,
            "salt": "MMAANNGGLLEE",
            "show_ir": False,
            "optimize": None,
            "document": False,
            "run": False,
            "time": False,
            "help": False,
        }
        flag = ""
        for raw_argument in sys.argv:
            argument = raw_argument.lower()
            if argument in {"-output", "-o", "-salt",
            "-sal", "-mangle", "-mang", "-source", "-s",
            "-opt", "-optimize", "-opt_level"}:
                flag = argument
            elif argument in {"--debug", "--dbg"}:
                self.arguments["debug"] = True
            elif argument in {"--show_ir", "--ir", "--llvm_ir"}:
                self.arguments["show_ir"] = True
            elif argument in {"--d", "--doc", "--docs", "--document", "--documentation"}:
                self.arguments["document"] = True
            elif argument in {"--r", "--run", "--execute", "--play"}:
                self.arguments["run"] = True
            elif argument in {"--time", "--t"}:
                self.arguments["time"] = True
            elif argument in {"--help", "--h"}:
                self.arguments["help"] = True
            elif flag in {"-output", "-o"}:
                self.arguments["output"] = argument
                flag = ""
            elif flag in {"-source", "-s"}:
                self.arguments["source"] = argument
                flag = ""
            elif flag in {"-salt", "-sal", "-mangle", "-mang"}:
                self.arguments["salt"] = argument
                flag = ""
            elif flag in {"-opt", "-optimize", "-opt_level"}:
                self.arguments["optimize"] = int(argument)
                flag = ""
        
        if self.arguments["source"] != None:
            with open(self.arguments["source"], "r") as file:
                src = file.read()
                self.tokenizer = Tokenizer(src, self.arguments["output"])

    def display_help(self):
        term_size = os.get_terminal_size().columns
        indent = ' '*10
        separator = lambda c: f"\n{c * term_size}\n"
        
        print(f"Intersect Programming Language v{VERSION}:".center(term_size, ":"))
        print(f"\n - Developed by William L.")
        print(f"\n\nCompiler Flags:{separator('=')}")
        
        print((
            f"{indent}-source | -s :".ljust(term_size) + f"The path/name of the source file to compile.".rjust(term_size) +
            separator('-') +
            f"{indent}-output | -o :".ljust(term_size) + f"The path/name of the binary file the compiler will output.".rjust(term_size) +
            separator('-') +
            f"{indent}--document | --d | --doc | --docs | --documentation :".ljust(term_size) + f"Generates HTML documentation for the given project based on docstrings.".rjust(term_size) + 
            separator('-')
        ))
        print(":" * term_size)

    def run(self):
        if self.arguments["help"]:
            self.display_help()
            exit()

        if self.arguments["debug"]:print("Tokenizing...")
        token_list = self.tokenizer.tokenize()
        
        tree = TreeBuilder(token_list, self.arguments["source"], self.arguments["salt"])

        # if self.arguments["debug"]:
        #     for token in token_list:
        #         tw = ""
        #         if token.type == SyntaxToken.string_literal:
        #             tw = "\""
        #         sys.stdout.write(f"{tw}{token.value}{tw}{' ' * (30 - len(str(token.value)))}{token.type.name}\n")
        if self.arguments["debug"]:print("Building Concrete Tree...")
        
        tree.parse_trunk()

        
        module = tree.get_module()

        if self.arguments["document"]:
            with open("./docs.html", "w") as fp:
                fp.write(module.get_documentation().replace("\0", ""))
        
        if self.arguments["run"] or self.arguments["output"] != None:
            if self.arguments["debug"]:print("Emitting LLVM IR...")
            module.write()

            if self.arguments["show_ir"]:
                module.dbg_print()
            if self.arguments["run"] or self.arguments["output"] != None:
                self.compile(module)

    def compile(self, module):
        import llvmlite.binding as llvm
        from ctypes import CFUNCTYPE, c_int, POINTER

        
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        llvm_module = llvm.parse_assembly(str(module))

        if self.arguments["optimize"] != None:
            # optimizer
            pm = llvm.create_module_pass_manager()
            pmb = llvm.create_pass_manager_builder()
            pmb.opt_level = self.arguments["optimize"]  # -O3
            pmb.populate(pm)

            # run optimizer

            # optimize
            pm.run(llvm_module)
        

        tm = llvm.Target.from_default_triple().create_target_machine(codemodel='default')
        # compile program
        with open(f"{self.arguments['output']}.o", "bw") as o_file:
            o_file_content = tm.emit_object(llvm_module)
            o_file.write(o_file_content)
        try:
            subprocess.run(["clang", f"{self.arguments['output']}.o", "-o", f"{self.arguments['output']}{'.exe' if platform.system() == 'Windows' else ''}"])
        except FileNotFoundError as e:
            print("Error: Intersect requires a working instalation of clang.  You can fix this by installing the Visual Studio C/C++ build tools found here: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2017")
        os.remove(f"{self.arguments['output']}.o")

        if self.arguments["run"]:
            if self.arguments["debug"]:print("PROGRAM RUNNING:")
            
            import time
            parameter = 5

            t0 = time.time()
            subprocess.run([f"{self.arguments['output']}{'.exe' if platform.system() == 'Windows' else ''}"])
            t1 = time.time()

            runtime = t1-t0
            if self.arguments["debug"] or self.arguments["time"]:print(f"runtime:{runtime*1000}ms")

        
