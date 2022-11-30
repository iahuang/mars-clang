import sys
from mips_clang.llvm_parse import parse
from mips_clang.clang import Clang
from mips_clang.llvm_translate import ll_as_mips
from mips_clang.pretty import prettyprint


with open(sys.argv[1]) as fl:
    clang = Clang()
    ll_source = clang.compile_to_ll(fl.read())
    
    print(ll_as_mips(ll_source))
    
