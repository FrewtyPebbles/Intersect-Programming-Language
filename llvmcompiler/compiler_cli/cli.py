import sys
from llvmcompiler.tree_builder import Tokenizer, SyntaxToken, TreeBuilder

class CLI:
    def __init__(self) -> None:
        self.arguments:dict[str,str|bool] = {
            "debug":False,
            "source":"./main.pop",
            "output":"./program",
            "salt": "MMAANNGGLLEE",
            "show_ir": False,
            "optimize": 1,
            "document": False,
            "run": False,
            "compile": False,
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
            elif argument in {"--c", "--compile", "--build", "--b"}:
                self.arguments["compile"] = True
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
        
        with open(self.arguments["source"], "r") as file:
            src = file.read()
            self.tokenizer = Tokenizer(src, self.arguments["output"])

    def run(self):
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
                fp.write(module.get_documentation())
        
        if self.arguments["compile"] or self.arguments["run"]:
            if self.arguments["debug"]:print("Emitting LLVM IR...")
            module.write()

            if self.arguments["show_ir"]:
                module.dbg_print()
            if self.arguments["run"]:
                self.compile(module)

    def compile(self, module):
        import llvmlite.binding as llvm
        from ctypes import CFUNCTYPE, c_int, POINTER


        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        llvm_module = llvm.parse_assembly(str(module))

        # optimizer
        pm = llvm.create_module_pass_manager()
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = self.arguments["optimize"]  # -O3
        pmb.populate(pm)

        # run optimizer

        # optimize
        pm.run(llvm_module)

        # print(llvm_module)


        tm = llvm.Target.from_default_triple().create_target_machine()


        # use this https://github.com/numba/llvmlite/issues/181 to figure out how to compile
        if self.arguments["debug"]:print("PROGRAM RUNNING:")
        with llvm.create_mcjit_compiler(llvm_module, tm) as ee:
            ee.finalize_object()
            fptr = ee.get_function_address("test")
            py_func = CFUNCTYPE(c_int, c_int)(fptr)
            import time
            parameter = 5

            t0 = time.time()
            ret_ = py_func(parameter)
            t1 = time.time()

            runtime = t1-t0
            if self.arguments["debug"]:print(f"Program returned: {ret_}")
            if self.arguments["debug"]:print(f"Compiled runtime:{runtime*1000}ms")

        
