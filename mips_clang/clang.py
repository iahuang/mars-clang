from dataclasses import dataclass
import os
import shutil
import subprocess
from . import fs
from . import util
from os.path import join

@dataclass
class CommandOutput:
    stdout: str
    stderr: str


def run_command(args: list[str]) -> CommandOutput:
    """Run a command, returning the output of the child process"""

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    stdout = util.with_unix_endl(stdout.decode("utf8"))
    stderr = util.with_unix_endl(stderr.decode("utf8"))

    return CommandOutput(stdout, stderr)

class Clang:
    _clang_path: str

    def __init__(self) -> None:
        self._clang_path = self._get_clang_path()

    def _get_clang_path(self) -> str:
        clang_path = shutil.which("clang")

        if not clang_path:
            raise RuntimeError(
                "MARS-Clang requires clang to be installed, but no such installation was found."
            )
        
        return clang_path
    
    def compile_to_ll(self, source: str) -> str:
        """
        Compile the contents of [source] as C/C++ code; return an LLVM source code
        string.
        """

        c_source_path = join(self.get_build_directory(), "tmp.c")
        llvm_source_path = "./tmp.ll"

        fs.write_file(
            path=c_source_path,
            data=source
        )

        result = run_command([self._clang_path, "-S", "-emit-llvm", "-m32", "-fno-slp-vectorize", c_source_path])
       
        if result.stderr:
            fs.write_file(
                path=join(self.get_build_directory(), "llvm_error.txt"),
                data=result.stderr
            )

            raise RuntimeError(
                "An unexpected error occurred during the compilation process. A detailed report has been written to {}".format(
                    self.get_build_directory()
                )
            )

        return fs.read_file(llvm_source_path)


    def get_build_directory(self) -> str:
        """
        MARS-Clang uses a temporary working "build" directory to store files needed for LLVM/Clang
        """
        cwd = os.getcwd()

        return join(cwd, "_build")