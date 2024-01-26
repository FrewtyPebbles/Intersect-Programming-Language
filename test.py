import platform
import subprocess as subp

TESTS:list[(str, None|str, str)] = [
    (
        "string",
        "hello\n",
        "hello\nMatch\n"
    ),
    (
        "vector",
        None,
        "Init called.\npushed data: 0, 1, 2\nvector top: 9999998\ncapacity: 16777216\nend.\n"
    ),
    (
        "realloc",
        None,
        "malloc 100\nrealloc1 200\nrealloc2 300\nvector data: 100, 200, 300\nend\n"
    ),
    (
        "node",
        None,
        "node_value: 1\nnode_value: 2\n"
    ),
    (
        "nested_struct",
        None,
        "Init called.\nget 0: 10\nget 0 and 1: 10 and 20\nend.\n"
    ),
    (
        "struct",
        None,
        "value: 5\n"
    ),
    (
        "hashmap",
        None,
        "thing one = 100\nthing two = 200\n"
    ),
    (
        "operator",
        None,
        "new_store: 3\n"
    ),
    (
        "vtable",
        None,
        "data: 5\ndata: 7\n"
    ),
    (
        "precision",
        None,
        "float: 390888.565894\n"
    )
]

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

def test_failed(name:str, input:str | None, expected:str, stdout:str, error:str):
    error = f'{Color.FAINT}Integration Test Error:{Color.END}\n{error}' if error != "" else ''
    stdout = stdout.replace('\r', 'Z').replace('\t', 'Z')
    return (
f"""
{Color.RED}Test{Color.END} [{Color.LIGHT_WHITE}{name}{Color.END}] {Color.RED}FAILED{Color.END}

{Color.FAINT}Expected:{Color.END}
{expected}
{Color.FAINT}Recieved:{Color.END}
{stdout}
{error}
""")
    

if __name__ == "__main__":
    failed_tests = []
    for name, usr_input, expected in TESTS:
        sp = subp.run(['py' if platform.system() == 'Windows' else 'python3', "main.py", "-s", f"./test/{name}.pop", "-o", f"./test_binaries/{name}", "--run"],
                      stdout=subp.PIPE, stderr=subp.PIPE,
                      input=usr_input.encode() if usr_input != None else None)
        stdout, stderr = sp.stdout, sp.stderr
        stdout, stderr = stdout.decode("utf-8").replace('\r', ''), stderr.decode("utf-8")
        if stdout == expected:
            print(f"\n{Color.GREEN}Passed Test{Color.END} [{Color.LIGHT_WHITE}{name}{Color.END}]\n")
        else:
            print(f"\n{Color.RED}FAILED Test{Color.END} [{Color.LIGHT_WHITE}{name}{Color.END}] {Color.RED}!!!{Color.END}\n")
            failed_tests.append(test_failed(name, usr_input, expected, str(stdout), stderr))
    
    if len(failed_tests) > 0:
        print(f"\n{Color.YELLOW}FAILED TESTS{Color.END} ({Color.LIGHT_WHITE}{len(failed_tests)}{Color.END}):\n")
        print("\n".join(failed_tests))
    else:
        print(f"{Color.GREEN}All tests passed!{Color.END}")