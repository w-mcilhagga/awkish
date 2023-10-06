# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 13:29:29 2023

@author: willi
"""

import os
import sys

# patch the path to access minawk as if it was installed
up = os.path.normpath(os.path.join(os.getcwd(), "../src"))
sys.path.append(up)
sys.path.append(os.getcwd())

# actual example here

import re
from miniawk import MiniAwk

# Example 1: Print all lines of a file

all_lines = MiniAwk()

@all_lines.on()
def printline(line):
    print(line)
    
# Example 2: Print the first 10 lines of a file

ten_lines = MiniAwk()

ten_lines.on(lambda nfr:nfr<10)(lambda line:print(line))


# Example 3: Count blank lines

blanks = MiniAwk()
nblanks = 0

@blanks.onmatch('^ *$')
def add():
    global nblanks
    nblanks += 1

@blanks.endfile
def report(fnr):
    print(f'{nblanks} blank lines out of {fnr}')
    

# Example 4: Remove all spaces.

nospace = MiniAwk()

@nospace.on()
def printnospaces(fields):
    print(''.join(fields))
    
# Example 5: print the longest line

# this uses globals
longest = MiniAwk()
linelen = -1
longest_line = None


@longest.on(lambda line:len(line)>linelen)
def savelong(line):
    global linelen, longest_line
    linelen = len(line)
    longest_line = line
    
@longest.end
def reportlongest():
    print(f'The longest line is {linelen} characters long:')
    print(longest_line)
    
# Example 5: 