# **Tarantula** A Compiled Lanugage Written In cPython

This is a compiler written in python that can be used to compose LLVM IR with syntax trees.


# Language Conventions

### Comments

**Tarantula** uses cPython style comments:

```py
# This is a comment
```

### Capitalization

In **Tarantula**, keywords that are used solely for implementation details such as *struct operators* or *error throwing* are fully capitalized.  Ex:

```rust
ERROR {
    show_line_number: false;
    show_file: false;
    show_parent_scope: true;
    "Variable value I would like to see durring my error": my_variable;
};
```

or

```rust
struct StructName<TemplateType> {

    heap_allocated_attribute: $TemplateType;

    # This right here!
    OPERATOR destructor(self) {
        delete self.heap_allocated_attribute;
        return
    }
}
```

### Automatic And Manual Memory Management

**Tarantula**'s automatic memory allocation is confined strictly to scope (more specifically to curly braces). `$` prefixes a *type* as a pointer type.  `heap` prefixes a *value* as a heap allocated value and allocates it on the heap.

```py
{
    let md_array: [$[i32]] = [
        heap [0,1,2],
        heap [0,1,2],
        heap [0,1,2]
    ];


    # md_array's heap allocated items are freed here
}
```

With the `persist` keyword, heap values can escape their scope, as exemplified below, but will need to be deleted manually eventually.

```py
# Create an array full of null pointers:
let outer_md_array: [$[i32 x 3] x 3] = []

{
    let md_array: [$[i32]] persist = [
        heap [0,1,2],
        heap [0,1,2],
        heap [0,1,2],
    ];

    outer_md_array[0] = md_array[0]
    outer_md_array[1] = md_array[1]
    outer_md_array[2] = md_array[2]
}

# All heap allocated items are freed here.
for (let i = 0; i < 3; i++) {
    delete outer_md_array[i]
}
```

You can either free each item of an object *manually as shown above*, or free the *entire object as shown below*:

```py
delete outer_md_array
```

***Keep in mind:*** freeing the entire array will call delete on every item of the array.  For structs, deleting the entire struct will call the `OPERATOR destructor` if it is implemented, if not it will free all heap members of the struct.

# TODO

### Implement Struct Operators:

 - Operator functions will be prefixed with the `OPERATOR` keyword rather than `func`

 - Destructor operator to decide how to handle memory when out of scope

    All heap allocated values are collected by default.

```rust
struct StructName {
    OPERATOR destructor(self) {
        delete self.heap_allocated_attribute;
    }
}
```

### Major Rework of Garbage Collector And How Heap is Allocated (Work in Progress):

```py
{
    let test_md_array: [$[i32]] persist = [
        heap [0,1,2],
        heap [0,1,2],
        heap [0,1,2],
        heap [0,1,2],
        heap [0,1,2]
    ];


    # test_md_array's heap allocated members are freed here at the end of its scope if persist is not used.
    # all heap values become null
}
```

The heap keyword should prefix values instead of variables.  This means that the garbage collector will need to free those values once the memory goes out of scope.
