from llvmcompiler.tree_builder import Token, SyntaxToken


"""
Problem:

Need to figure out how to order my operations.

Ex:
    5 - 2 - func(8 % var + 7 * 2) * 9 - 2

Solution: get all possible operations and place them in a stack:

    "p(n)" is used to represent some type of parentheses equivalent.

            [(5 - 2)(2 - p1)(p1 * 9)(9 - 2)]

    then

            p1 = func[(8 % var)(var + 7)(7 * 2)]

    Each operation is given its priority, operations with "p(n)" are added to an execution stack before those arround it.

            [(5 - 2)(2 - p1)(p1 * 9)(9 - 2)]
                2      3        1      4

            then

            p1 = func[(8 % var)(var + 7)(7 * 2)]
                         1         3       2

    prioritized operations will replace, within the operation prioritized closest below/after them that shares a common value, the value that they share with them.

            p1 = func[( (8 % var) + (7 * 2) )]

    then

            [( ( (5 - 2) - (p1 * 9) ) - 2)]

            
Requirements for this to work:

    - The values will need to be wrapped in an object that maintains references to where they are in the operations
    to the left and right of the current operation so the current operation can replace the values it shares to its left and right.

    - When giving operations their priority, we will perform a scan of the list of potential operations from left to right for each operation type that exists in the language.
    The operation priority starts at 1, and priority numbers are only given to operations that are the same as the current scan's operation type. each time a priority is given,
    the priority number given to the next operation that recieves a priority number is incremented by 1. The current priority number is not reset between scans.
"""

