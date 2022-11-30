from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .util import ltrim, ltrim_regex, rtrim, unwrap, with_unix_endl
import re

TYPE_PATTERN = r'\w+\*{0,}'
FUNCTION_PATTERN = r'@\w+'
REGISTR_PATTERN = r'%\w+'

@dataclass
class LLVMInstruction:
    name: str
    mode: Optional[str] = None
    associated_type: Optional[LLVMType] = None
    args: list[LLVMSymbol] = field(default_factory=list)


@dataclass
class LLVMFunction:
    statements: list[LLVMStatement]
    return_type: LLVMType
    name: str

@dataclass
class LLVMStatement:
    """
    Examples:
    ```
    %1 = alloca i32, align 4
    ```
    and
    ```
    store i32 %27, i32* %2, align 4
    ```
    """

    _assign_to: Optional[LLVMSymbol]
    _instruction: Optional[LLVMInstruction]
    _label: Optional[str]

    @staticmethod
    def from_label(label_name: str) -> LLVMStatement:
        return LLVMStatement(_assign_to=None, _instruction=None, _label=label_name)
    
    @staticmethod
    def from_assignment(to: LLVMSymbol, instruction: LLVMInstruction) -> LLVMStatement:
        return LLVMStatement(_assign_to=to, _instruction=instruction, _label=None)
    
    @staticmethod
    def from_instruction(instruction: LLVMInstruction) -> LLVMStatement:
        return LLVMStatement(_assign_to=None, _instruction=instruction, _label=None)

    def get_instruction(self) -> LLVMInstruction:
        return unwrap(self._instruction)

    def get_label_name(self) -> str:
        assert self.is_label()
        return unwrap(self._label)
    
    def get_assignment_target(self) -> LLVMSymbol:
        assert self.is_assignment()
        return unwrap(self._assign_to)
    
    def is_assignment(self) -> bool:
        return self._assign_to is not None
    
    def is_label(self) -> bool:
        return self._label is not None
    

class LLVMType:
    type_name: str
    
    pointer: int
    """
    `0` if this type is not a pointer,
    `1` if this type is a pointer,
    `2` if this type is a pointer to a pointer, and so on.
    """

    def __init__(self, from_type_string: str) -> None:
        from_type_string = from_type_string.strip()
        # for instance, separate "i32**" into "i32" and "**"
        self.type_name, other = unwrap(ltrim_regex(from_type_string, r'\w+'))
        
        self.pointer = other.count("*")
    
    @staticmethod
    def any() -> LLVMType:
        return LLVMType("any")
    
    def is_any(self) -> bool:
        return self.type_name == "any"

    def __str__(self) -> str:
        return "<LLVMType {}>".format(self.type_name+("*"*self.pointer))
        

REGISTER = 0
CONSTANT = 1
GLOBAL = 2

class LLVMSymbol:
    _content: str
    _type: LLVMType
    _symbol_type: int

    def __init__(self, type: LLVMType, symbol_str: str) -> None:
        self._type = type

        if symbol_str.startswith("%"):
            symbol_str = ltrim(symbol_str, "%")
            
            self._content = symbol_str
            self._symbol_type = REGISTER
        elif symbol_str.startswith("@"):
            symbol_str = ltrim(symbol_str, "@")
            self._content = symbol_str
            self._symbol_type = GLOBAL
        else:
            self._content = symbol_str
            self._symbol_type = CONSTANT
    
    def __str__(self) -> str:
        return "<LLVMSymbol content={} type={} symbol_type={}>".format(repr(self._content), self._type, self._symbol_type)
        
    def get_register_name(self) -> str:
        if not self.is_register():
            raise ValueError("Symbol is not a register")
        return self._content
    
    def get_constant_value(self) -> int:
        if not self.is_constant():
            raise ValueError("Symbol is not a constant")
        
        return eval(self._content)
    
    def is_register(self) -> bool:
        return self._symbol_type == REGISTER
    
    def is_constant(self) -> bool:
        return self._symbol_type == CONSTANT
    
    def is_global(self) -> bool:
        return self._symbol_type == GLOBAL
    
    def get_type(self) -> LLVMType:
        return self._type
    
    @staticmethod
    def from_argument(argument_string: str, disallow_any=False) -> LLVMSymbol:
        """
        Turn an LLVM Instruction comma-separated argument as a string into an `LLVMSymbol` object

        Some examples of `argument_string`:
        - `"i32 %4"`
        - `"i32 0"`
        - `"32"`
        - `"i32* inttoptr (i32 4 to i32*)"`
        """

        parts = argument_string.split(" ")
        if len(parts) == 1:
            if disallow_any: raise ValueError("Invalid argument string \"{}\" (any not allowed)".format(argument_string))
            return LLVMSymbol(LLVMType.any(), parts[0])
        if len(parts) == 2:
            type, name = parts
            return LLVMSymbol(LLVMType(type), name)
        if parts[1] == "inttoptr": # e.g. "i32* inttoptr (i32 4 to i32*)"
            # separate "i32*" from "inttopotr (..."
            type_string, argument_string = unwrap(ltrim_regex(argument_string, TYPE_PATTERN))
            argument_string = argument_string.strip()

            # remove "inttoptr"
            argument_string = ltrim(argument_string, "inttoptr").strip()
            # find and remove parentheses
            assert argument_string.startswith("(") and argument_string.endswith(")")
            argument_string = argument_string[1:-1]

            # split conversions ("i32 4 to i32*" to ["i32 4", "i32*"])
            int_symbol, ptr_type = argument_string.split(" to ")
            int_value = LLVMSymbol.from_argument(int_symbol).get_constant_value()
            return LLVMSymbol(LLVMType(ptr_type), str(int_value))

        raise ValueError("Invalid argument string \"{}\"".format(argument_string))

class _LLVMParser:
    source: str
    _lines: list[str]
    
    _line_index: int
    """Stores the current line position in the file"""

    def __init__(self, source: str) -> None:
        self.source = source
        self._lines = with_unix_endl(self.source).split("\n")
        self._line_index = 0
    
    def next_line(self) -> bool:
        self._line_index += 1

        return self.has_next_line()
    
    def has_next_line(self) -> bool:
        return self._line_index < len(self._lines)

    def get_current_line(self) -> str:
        if not self.has_next_line():
            raise EOFError()

        return self._lines[self._line_index]
    
    def peek_next_line(self) -> str:
        return self._lines[self._line_index + 1]
    
    def parse(self) -> list[LLVMFunction]:
        functions: list[LLVMFunction] = []

        while self.has_next_line():
            line = self.get_current_line()

            if line.startswith("define "):
                function = self.parse_function_decl()
                functions.append(function)

            self.next_line()
        
        return functions
    
    def parse_function_decl(self) -> LLVMFunction:
        """
        Current line position should be set to the function header line

        (e.g. `"define void @main() #0 {"`)
        """

        header = self.get_current_line()
        # remove the leading "define" keyword, and remove any whitespace
        header = ltrim(header, "define").strip()
        # parse out the type string (e.g. "i32*") and remove whitespace
        return_type_string, header = unwrap(ltrim_regex(header, TYPE_PATTERN))
        header = header.strip()
        # parse out the name of the function, and remove any whitespace
        function_name, header = unwrap(ltrim_regex(header, FUNCTION_PATTERN))

        return_type = LLVMType(return_type_string)
        
        self.next_line()

        statements: list[LLVMStatement] = []

        while True:
            line = self.get_current_line()
            if line == "}":
                break

            statement = self.parse_statement(line)

            if statement:
                statements.append(statement)

            self.next_line()
        
        return LLVMFunction(
            statements=statements,
            return_type=return_type,
            name=function_name
        )
    
    def parse_statement(self, line: str) -> Optional[LLVMStatement]:
        line = line.strip()

        if line == "":
            return None
        if re.match(r'\w+:', line):
            return LLVMStatement.from_label(rtrim(line, ":"))
        if re.match(REGISTR_PATTERN + r' {0,}=', line):
            register_str, line = unwrap(ltrim_regex(line, REGISTR_PATTERN))
            _, line = unwrap(ltrim_regex(line, r' {0,}= {0,}'))

            return LLVMStatement.from_assignment(
                to=LLVMSymbol.from_argument(register_str),
                instruction=self.parse_instruction(line)
            )
            
        return LLVMStatement.from_instruction(self.parse_instruction(line))
    
    def parse_instruction(self, line: str) -> LLVMInstruction:
        instruction_name, line = unwrap(ltrim_regex(line, r'\w+'))
        line = line.strip()
        args = line.split(",")

        # remove leading and trailing whitespace from unparsed argument strings
        args = [arg.strip() for arg in args]

        if instruction_name == "alloca":
            return LLVMInstruction(
                name=instruction_name,
                associated_type=LLVMType(args[0])
            )
        if instruction_name == "store":
            return LLVMInstruction(
                name=instruction_name,
                args=[LLVMSymbol.from_argument(args[0]), LLVMSymbol.from_argument(args[1])]
            )
        if instruction_name == "load":
            return LLVMInstruction(
                name=instruction_name,
                associated_type=LLVMType(args[0]),
                args=[LLVMSymbol.from_argument(args[1])]
            )
        if instruction_name == "add" or instruction_name == "sub":
            mode = None

            if args[0] == "nsw" or args[0] == "nuw":
                args.pop()
       
            if args[0] == "nsw" or args[0] == "nuw":
                args.pop()


            return LLVMInstruction(
                name=instruction_name,
                mode=mode,
                args=[LLVMSymbol.from_argument(args[0]), LLVMSymbol.from_argument(args[0])]
            )
        if instruction_name == "ret":
            return LLVMInstruction(
                name=instruction_name,
                args=[LLVMSymbol.from_argument(args[0])]
            )
        if instruction_name == "getelementptr":
            # if the "inbounds" specifier is present, remove it
            if args[0] == "inbounds":
                args.pop(0)
            
            type = LLVMType(args[0])

            return LLVMInstruction(
                name=instruction_name,
                associated_type=type,
                args=[LLVMSymbol.from_argument(args[1]), LLVMSymbol.from_argument(args[2])]
            )

        raise SyntaxError("Unsupported LLVM IR instruction \"{}\"".format(instruction_name))


def parse(source: str) -> list[LLVMFunction]:
    return _LLVMParser(source).parse()