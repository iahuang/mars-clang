from mips_clang.util import ltrim
from .llvm_parse import LLVMFunction, LLVMSymbol, LLVMType, parse

def get_sizeof(type: LLVMType) -> int:
    """Return the size of the given type in bytes"""

    if type.pointer:
        # MARS uses MIPS32
        return 4
    if type.type_name == "i32":
        return 4
    if type.type_name == "i8":
        return 1
    
    raise ValueError("Unrecognized type \"{}\"".format(type.type_name))

def function_name_as_mips_label(function_name: str) -> str:
    assert function_name.startswith("@")
    return "__func_"+ltrim(function_name, "@")

class _LLVMTranslator:
    source: str
    functions: list[LLVMFunction]

    def __init__(self, ll_source: str) -> None:
        self.source = ll_source
        self.functions = parse(ll_source)

    def translate(self) -> str:
        output = ""

        for function in self.functions:
            output += self.translate_function(function) + "\n"
        
        return output
    
    def get_function(self, name: str) -> LLVMFunction:
        for f in self.functions:
            if f.name == name:
                return f
        raise ValueError("No function with name \"{}\"".format(name))
    
    def translate_function(self, function: LLVMFunction) -> str:
        """
        See `docs/calling_convention.txt` for more information
        """
        
        output: list[str] = []

        # if this is the main function, add the ".text" label
        if function.name == "@main":
            output.append(".text")

        # 4 bytes are needed on the stack to store the return address
        stackframe_size = 4

        registers: dict[str, LLVMSymbol] = {}
        # maps register names to corresponding stack pointer offsets
        register_sp_offsets: dict[str, int] = {}

        # begin by identifiying all registers used
        for statement in function.statements:
            if statement.is_assignment():
                assign_to = statement.get_assignment_target()
                registers[assign_to.get_register_name()] = assign_to
                register_sp_offsets[assign_to.get_register_name()] = stackframe_size
                stackframe_size += 4

        # add instruction to allocate space on the stack
        output.append("addiu $sp,$sp,-{}".format(stackframe_size))
        
        # add instruction to save the return address
        output.append("sw $ra,($sp)")

        # translate instructions
        for statement in function.statements:
            if statement.is_label():
                output.append(statement.get_label_name() + ":")
                continue

            # assume statement contains an instruction
            instruction = statement.get_instruction()
            iname = instruction.name
            # print(iname)
            # print([str(arg) for arg in instruction.args])
            instruction_text = iname + " " + " ".join(
                str(arg.get_constant_value()) if arg.is_constant() else "%"+arg.get_register_name()
                for arg in instruction.args
            )
            output.append("")
            if statement.is_assignment():
                output.append("# %{} = {}".format(
                    statement.get_assignment_target().get_register_name(),
                    instruction_text
                ))
            else:
                output.append("# {}".format(instruction_text))

            # for LLVM instructions like "load", which have an output, the output
            # gets stored in $t7. this variable is set to `True`, if the LLVM instruction
            # produced an output.
            instruction_has_output = False

            if iname == "alloca":
                # alloca always exists in the context of a register assignment.
                # get the register we're assigning to
                target_register = statement.get_assignment_target().get_register_name()

                # we've already pre-allocated space on the stack for this register
                # assign the value of this register to its own address
                output.append("move $t7,$sp")
                output.append("addu $t7,$t7,{}".format(register_sp_offsets[target_register]))

                instruction_has_output = True
            elif iname == "store":
                stored_value = instruction.args[0]
                store_to = instruction.args[1]
                assert store_to.is_register()

                # $t1 contains the value being stored
                # $t2 contains the address being stored to (the pointer contained inside the target
                # register)

                if stored_value.is_constant():
                    output.append("li $t1,{}".format(stored_value.get_constant_value()))
                else:
                    output.append("lw $t1,{}($sp)".format(
                        register_sp_offsets[stored_value.get_register_name()])
                    )
                output.append("lw $t2,{}($sp)".format(
                    register_sp_offsets[store_to.get_register_name()])
                )
                output.append("sw $t1,($t2)".format())
            elif iname == "load":
                target = instruction.args[0]
                output.append("lw $t7,{}($sp)".format(
                    register_sp_offsets[target.get_register_name()]
                ))

                instruction_has_output = True
            elif iname == "ret":
                # free allocated stack space
                output.append("addiu $sp,$sp,{}".format(stackframe_size))
                # return
                output.append("jr $ra")
            else:
                raise NotImplementedError("Unsupported instruction \"{}\"".format(iname))

            if statement.is_assignment():
                # we can only assign to values of LLVM instructions that produce an output
                assert instruction_has_output
                target_register_name = statement.get_assignment_target().get_register_name()
                output.append("sw $t7,{}($sp)".format(register_sp_offsets[target_register_name]))

            
        # indent output and add subroutine label
        indented = "\n".join("    " + line for line in output)
        return function_name_as_mips_label(function.name) + ":\n" + indented

def ll_as_mips(ll_source: str) -> str:
    return _LLVMTranslator(ll_source).translate()