# mars-clang

LLVM/Clang target implementation for MARS MIPS Simulator

Enables compilation from C/C++ to MIPS code that can run in [MARS](http://courses.missouristate.edu/kenvollmar/mars/), a MIPS assembly emulator used in [CSC258H1: Computer Organization](https://artsci.calendar.utoronto.ca/course/csc258h1) at the University of Toronto.

## Usage

Clang must be installed on your system for `mars-clang` to work. If the command `clang --version` works (as exactly written), then `mars-clang` will be able to use your distribution of Clang. `mars-clang` has been tested on Python 3.10.
```
python3 mars-clang.py [input_file] > build.mips
```

## Example Program

Draw two red pixels on the MARS bitmap display.
```c
#define RED 0x00ff0000
#define BITMAP_PTR (int*)0x10008000

int main() {
    int* pixel = BITMAP_PTR;
    *pixel = RED;
    pixel += 4;
    *pixel = RED;

    return 0;
}
```

## Support Table

The way `mars-clang` works is by using `clang` to compile a C/C++ program to [LLVM IR](https://llvm.org/docs/LangRef.html#introduction) code and then translating that code into MIPS line-by-line. Hence, only some LLVM IR instructions are currently supported.

| LLVM Instruction | MIPS Translation Support |
|------------------|--------------------------|
| `alloca`         | **Full support**         |
| `store`          | **Partial support**      |
| `load`           | **Partial support**      |
| `getelementptr`  | **Partial support**      |
| `ret`            | **Incomplete support**   |

Note that "Partial support" means that while the entire functionality of the LLVM IR instruction may not be supported, most of or all of the cases in which the instruction is used in *LLMV-generated* code are supported. 

"Incomplete support" means that the presence of the instruction will not cause `mars-clang` to crash, but the functionality of the instruction is incomplete.