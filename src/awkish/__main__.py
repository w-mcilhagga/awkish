"""
command-line usage of awkish
"""

import os
import sys
up = os.path.normpath(os.path.join(os.getcwd(), "../src"))
sys.path.append(up)
sys.path.append(os.getcwd())

from awkish import Awk
import argparse
import runpy

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

parser.add_argument('awkprog') 
parser.add_argument('inputs', nargs='+')
parser.add_argument('-o', '--output')


if __name__=='__main__':
    args = parser.parse_args()
    # load argprog
    print(args.awkprog)
    prog = runpy.run_path(args.awkprog)#.replace('.py',''))
    awk = None
    for name in prog:
        if type(prog[name]) is Awk:
            awk = prog[name]
            break
    if awk is None:
        print('No awk object defined')
        sys.exit(1)
    # run it on inputs
    awk(*args.inputs, output=args.output)