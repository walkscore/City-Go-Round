import sys

def BREAKPOINT():
    import pdb
    p = pdb.Pdb(None, sys.__stdin__, sys.__stdout__)
    p.set_trace()
