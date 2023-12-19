from __future__ import annotations
from types import NoneType
from llvmcompiler import Value, I32Type, F32Type,\
    D64Type, BoolType, C8Type, ArrayType
from llvmcompiler.ir_renderers.operations import *
import llvmcompiler.tree_builder as tb
#tb.Token, SyntaxToken


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
class OperationsOrder:
    def __init__(self, potential_operations: list[PotentialOperation | OperationsOrder] = None) -> None:
        self.potential_operations = [] if potential_operations == None else potential_operations
        self._priority_stack: list[PotentialOperation | OperationsOrder] = []
        self._result:PotentialOperation = None
        
    
    def get_priority_stack(self):
        # (5 - 2)(2 - p1)(p1 * 9)(9 - 2)
        #    2      3        1      4
        current_priority = 15
        while len(self._priority_stack) != len(self.potential_operations):
            for potential_op in reversed(self.potential_operations):
                if current_priority == potential_op.priority:
                    self._priority_stack.append(potential_op)

            current_priority -= 1

    def combine_priority_stack(self):
        top = self._priority_stack.pop()
        while len(self._priority_stack):
            

            below = self._priority_stack.pop()
            below.replace_common(top)
            top = below
        
        self._result = top

    def get_tree(self):
        self.get_priority_stack()
        self.combine_priority_stack()
        return self._result.get_tree()
            

class PotentialOperation:
    def __init__(self, values:list[OpValue | PotentialOperation], op:tb.Token):
        self.op = op
        self.values = values

    def replace_common(self, replacement:PotentialOperation):
        for val_ind, val in enumerate(self.values):
            if val in replacement.values:
                self.values[val_ind] = replacement
                break

        
    @property
    def priority(self):
        if self.op == None:
            return 1
        return self.op.priority

    def __repr__(self) -> str:
        return f"(PO : {{values: {self.values}, op: {self.op}}})"
    
    def get_tree(self):
        values = []
        for val_n, val in enumerate(self.values):
            if isinstance(val, OpValue):
                values.append(val.get_value())
            else:
                values.append(val.get_tree())

        if self.op == None:
            # None means that it is the only value
            return values[0]


        match self.op.type:
            case tb.SyntaxToken.add_op:
                return AddOperation(values)
            case tb.SyntaxToken.subtract_op:
                return SubtractOperation(values)
            case tb.SyntaxToken.multiply_op:
                return MultiplyOperation(values)
            case tb.SyntaxToken.divide_op:
                return DivideOperation(values)
            case tb.SyntaxToken.modulo_op:
                return ModuloOperation(values)
            case tb.SyntaxToken.assign_op:
                return ModuloOperation(values)
            case tb.SyntaxToken.less_than_op:
                return LessThanOperation(values)
            case tb.SyntaxToken.greater_than_op:
                return GreaterThanOperation(values)
            case tb.SyntaxToken.greater_than_or_equal_to_op:
                return GreaterThanOrEqualToOperation(values)
            case tb.SyntaxToken.less_than_or_equal_to_op:
                return LessThanOrEqualToOperation(values)
            case tb.SyntaxToken.equal_to_op:
                return EqualToOperation(values)
            case tb.SyntaxToken.not_equal_to_op:
                return NotEqualToOperation(values)
            case tb.SyntaxToken.or_op:
                return OrOperation(values)
            case tb.SyntaxToken.and_op:
                return AndOperation(values)
            case tb.SyntaxToken.cast_op:
                return CastOperation(values)
            case tb.SyntaxToken.dereference_op:
                return DereferenceOperation(values)
            case tb.SyntaxToken.sizeof_op:
                #print(f"EMIT SIZEOF OPERATION {values}")
                return TypeSizeOperation(values)
            case tb.SyntaxToken.not_op:
                return NotOperation(values)
            case tb.SyntaxToken.post_increment_op:
                # not implemented yet
                pass
            case tb.SyntaxToken.post_decrement_op:
                # not implemented yet
                pass
        

class OpValue:
    def __init__(self, value:tb.Token | Operation):
        self.value = value

    def __repr__(self) -> str:
        if all([not isinstance(self.value, typ) for typ in {Operation, Value, str, CompilerType, NoneType}]):
            #print("val.val")
            return f"(OPVAL : {self.value.value})"
        elif isinstance(self.value, str):
            #print("val")
            return f"(OPVAL : {self.value})"
        else:
            return f"(OPVAL : {type(self.value)})"

    def get_value(self):
        #print(self.value)
        if any([isinstance(self.value, typ) for typ in {Operation, Value, CompilerType, str}]):
            return self.value
        return get_value_from_token(self.value)

def get_value_from_token(value:tb.Token):
    if value.type.is_literal or value.type == tb.SyntaxToken.label:
        return value.compiler_value
    elif value.type.is_type:
        return value.compiler_type
