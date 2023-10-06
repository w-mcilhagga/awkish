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

myawk = MiniAwk(FS=re.compile(" +"))

@myawk.begin
def begin(nr):
    print("begin")

@myawk.beginfile
def beginf(filename):
    print("\nbegin", filename)

@myawk.on(lambda f0: f0 != "")
def printline(fields):
    print(" ".join(fields), end="")

@myawk.on(lambda f2=1: int(f2) % 2 == 0)
def doline(nr, f2):
    # difference between fields[n] and fn is that fn is None if it
    # isn't there but fields[n] raises an exception.
    print(" ***", f2, nr, end="")

@myawk.on(lambda line: line != "")
def printend():
    # terminates a line
    print()

@myawk.end
def end():
    print("\nend")

myawk("../tests/mawktest.txt", "../tests/mawktest.txt")