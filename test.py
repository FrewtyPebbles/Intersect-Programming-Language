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

def test_failed(name:str, input:str | None, expected:str, stdout:str, error:str):
    error = f'Integration Test Error:\n{error}' if error != "" else ''
    stdout = stdout.replace('\r', 'Z').replace('\t', 'Z')
    return (
f"""

test [{name}] FAILED

Expected:
{expected}
Recieved:
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
            print(f"\nPassed Test [{name}]\n")
        else:
            print(f"\nFAILED Test [{name}] !!!\n")
            failed_tests.append(test_failed(name, usr_input, expected, str(stdout), stderr))
    
    if len(failed_tests) > 0:
        print(f"\nFAILED TESTS ({len(failed_tests)}):\n")
        print("\n".join(failed_tests))
    else:
        print("All tests passed!")