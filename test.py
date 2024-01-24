import subprocess as subp
TESTS = [
    (
        "string",
        "hello\nMatch",
        "hello"
    ),
    (
        "vector",
        None,
        "Init called.\npushed data: 0, 1, 2\nvector top: 9999998\ncapacity: 16777216\nend."
    ),
    (
        "realloc",
        None,
        "malloc 100\nrealloc1 200\nrealloc2 300\nvector data: 100, 200, 300\nend"
    ),
    (
        "node",
        None,
        "node_value: 1\nnode_value: 2"
    ),
    (
        "nested_struct",
        None,
        "Init called.\nget 0: 10\nget 0 and 1: 10 and 20\nend."
    ),
    (
        "struct",
        None,
        "value: 5"
    ),
    (
        "hashmap",
        None,
        "thing one = 100\nthing two = 200"
    ),
    (
        "operator",
        None,
        "new_store: 3"
    ),
    (
        "vtable",
        None,
        "data: 5\ndata: 7"
    ),
    (
        "precision",
        None,
        "float: 390888.565894"
    )
]

def test_failed(name:str, input:str | None, expected:str, stdout:str, error:str):
    error = f'Compiler Error:\n{error}' if error != "" else ''
    return (
f"""test [{name}] FAILED

Expected:
{expected}
Recieved:
{stdout}
{error}
""")
    

if __name__ == "__main__":
    for name, input, expected in TESTS:
        sp = subp.Popen(["python3", "main.py", "-s", f"./test/{name}.pop", "-o", f"./test_binaries/{name}", "--run"], stdout=subp.PIPE, stderr=subp.PIPE)
        stdout = ""
        stderr = ""
        if input != None:
            stdout, stderr = sp.communicate(input)
        else:
            stdout, stderr = sp.communicate()
        stdout, stderr = stdout.decode("utf-8"), stderr.decode("utf-8")
        assert stdout == expected, test_failed(name, input, expected, str(stdout), stderr)