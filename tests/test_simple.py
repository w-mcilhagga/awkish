"""
tests
"""

import filecmp as fc
import os
import sys
up = os.path.normpath(os.path.join(os.getcwd(), "../src"))
sys.path.append(up)
sys.path.append(os.getcwd())

from awkish import Awk


def test_simple():
    # echo
    awk = Awk()
    awk.when(True)()
    awk("inputs/awktest1.txt", output="awkresult.txt")
    assert fc.cmp("inputs/awktest1.txt", "awkresult.txt")
    os.remove("awkresult.txt")


def test_nfr():
    # every second line
    awk = Awk()
    awk.when(lambda nfr: nfr % 2 == 0)()
    awk("inputs/awktest1.txt", output="awkresult.txt")
    assert fc.cmp("awkresult.txt", "outputs/awkresult_nfr.txt")
    os.remove("awkresult.txt")


def test_nfr2():
    # test of end condition
    global value
    awk = Awk()
    @awk.end
    def storeval(nfr):
        global value
        value=nfr
    awk("inputs/awktest1.txt")
    assert(value==5)

def test_fields():
    # switch fields, tests defaults
    awk = Awk()
    awk.when(True)(lambda f1='', f2='':print(f2+','+f1))
    awk("inputs/awktest1.txt", output="awkresult.txt")
    assert fc.cmp("awkresult.txt", "outputs/awkresult_fields.txt")
    os.remove("awkresult.txt")