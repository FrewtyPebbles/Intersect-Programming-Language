import os
import platform
import subprocess
import sys
from llvmcompiler.tree_builder import Tokenizer, SyntaxToken, TreeBuilder

VERSION = "0.1.0"

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
                self.tokenizer = Tokenizer(src, self.arguments["output"], self.arguments["source"])

    def display_help(self):
        term_size = os.get_terminal_size().columns
        indent = ' '*10
        separator = lambda c: f"\n{c * term_size}\n"

        flag_color = Color.YELLOW
        def_color = Color.LIGHT_WHITE
        
        print(f"Intersect Programming Language v{VERSION}")
        print(f" - Developed by William L.")
        print(f"COMPILER FLAGS:")
        print()
        flag_sep = f"\n{separator('╲')}\n"
        
        print((
            f"{indent}{flag_color}-source | -s :".ljust(term_size) +
            f"{Color.END}The path/name of the source file to compile.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}-output | -o :".ljust(term_size) +
            f"{Color.END}The path/name of the binary file the compiler will output.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}--document | --d | --doc | --docs | --documentation :".ljust(term_size) +
            f"{Color.END}Generates HTML documentation for the given source code based on docstrings.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}--run | --r | --execute | --play :".ljust(term_size) +
            f"{Color.END}Compiles and runs the provided source code.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}--time | --t :".ljust(term_size) +
            f"{Color.END}Times your program's total runtime.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}-optimize | -opt | -opt_level :".ljust(term_size) +
            f"{Color.END}Specifies the llvm optimization level.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}-salt | -sal | -mangle | -mang :".ljust(term_size) +
            f"{Color.END}Specifies the string to use when mangling namespaces in the compiled binary or library.".rjust(term_size) +
            flag_sep +
            f"{indent}{flag_color}--show_ir | --ir | --llvm_ir :".ljust(term_size) +
            f"{Color.END}Shows the llvm ir that your program compiles to.".rjust(term_size) +
            "\n"
        ))
        exit()

    def run(self):
        if self.arguments["help"]:
            self.display_help()
            exit()

        if self.arguments["debug"]:print("Tokenizing...")
        token_list = self.tokenizer.tokenize()
        
        tree = TreeBuilder(token_list, self.arguments["source"], self.arguments["salt"])

        if self.arguments["debug"]:
            for token in token_list:
                tw = ""
                if token.type == SyntaxToken.string_literal:
                    tw = "\""
                sys.stdout.write(f"{tw}{token.value}{tw}{' ' * (30 - len(str(token.value)))}{token.type.name}\n")
        if self.arguments["debug"]:print("Building Concrete Tree...")
        
        tree.parse_trunk()

        
        module = tree.get_module()

        if self.arguments["document"]:
            with open("./docs.html", "w") as fp:
                fp.write(module.get_documentation().replace("\0", ""))
        
        if self.arguments["run"] or self.arguments["output"] != None:
            if self.arguments["debug"]:print("Emitting LLVM IR...")
            module.write()

            
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
            print("ERROR:\n\tCompiling a program with Intersect requires a working instalation of clang.\n\nYou can fix this by installing the Visual Studio C/C++ build tools found here: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2017")
            exit()

        os.remove(f"{self.arguments['output']}.o")

        if self.arguments["show_ir"]:
            print(llvm_module)
        
        if self.arguments["run"]:
            if self.arguments["debug"]:print("PROGRAM RUNNING:")
            
            import time
            parameter = 5

            t0 = time.time()
            subprocess.run([f"{self.arguments['output']}{'.exe' if platform.system() == 'Windows' else ''}"])
            t1 = time.time()

            runtime = t1-t0
            if self.arguments["debug"] or self.arguments["time"]:print(f"runtime:{runtime*1000}ms")

        
