# mars-clang

LLVM/Clang target implementation for MARS MIPS Simulator

Enables compilation from C/C++ to MIPS code that can run in [MARS](http://courses.missouristate.edu/kenvollmar/mars/), a MIPS assembly emulator used in [CSC258H1: Computer Organization](https://artsci.calendar.utoronto.ca/course/csc258h1) at the University of Toronto.

## Usage

```
python3 mips-clang.py [input_file] > build.mips
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