# -*- coding: utf-8 -*-
"""
Created on Sun Oct 15 16:16:26 2023

@author: willi
"""
import filecmp as fc
import os
import sys

up = os.path.normpath(os.path.join(os.getcwd(), "../src"))
sys.path.append(up)
sys.path.append(os.getcwd())
from awkish import Awk

# line endings are an issue with echo & similar

# ---------------------------------------------------
# echo


def test_echo():
    a = Awk()
    a.all()
    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/echo.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# echo+args


def test_param():
    a = Awk()
    a.all(lambda self: self.print(self.prefix+self.line))
    a.prefix = '>>> '
    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/echo2.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# select some fields


def test_select():
    a = Awk(FS=Awk.CSV, OFS=",")

    @a.when(True)
    def select(self):
        print(self.f1, self.f3, sep=self.OFS)

    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/select.txt", "result.txt")
    os.remove("result.txt")
    
# ---------------------------------------------------
# save range of lines

def test_range():
    # lines in range
    a = Awk()
    a.when(lambda self: self.nr>1 and self.nr<=4)()
    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/range.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# search for a string & print lines


def test_find():
    a = Awk()
    a.when(Awk.find("sonia"))()
    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/find.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# search for a regular expression & print lines


def test_search():
    a = Awk()
    a.when(Awk.search(":+"))()
    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/search.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# summing the values in field 1


def test_sum():
    a = Awk(FS=Awk.CSV, OFS=",")

    @a.begin
    def begin(self):
        self.sum = 0

    @a.when(lambda self: self.nfr > 1)
    def sumf1(self):
        self.sum += float(self.f1)

    @a.end
    def printsum(self):
        print("sum = ", self.sum)

    a("inputs/data.txt", output="result.txt")
    assert fc.cmp("outputs/sum.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# remove dups

def test_duplicates():
    a = Awk()
    a.lcount = {}

    @a.when(True)
    def procline(self):
        self.lcount[self.line] = self.lcount.get(self.line, 0) + 1

    @a.end
    def printu(self):
        for line in self.lcount:
            self.print(line)

    a("inputs/repeats.txt", output="result.txt")
    assert fc.cmp("outputs/nodups.txt", "result.txt")
    os.remove("result.txt")
    
# ---------------------------------------------------
# word usage counts


def test_usage():
    a = Awk(FS=re.compile("\W+"))
    a.wcount = {}

    @a.when(True)
    def wcount(self):
        for f in self.fields:
            f = f.lower()
            self.wcount[f] = self.wcount.get(f, 0) + 1

    @a.end
    def printw(self):
        for word in self.wcount:
            print(word, self.wcount[word])

    a("inputs/passage.txt", output="result.txt")
    assert fc.cmp("outputs/usage.txt", "result.txt")
    os.remove("result.txt")

# ---------------------------------------------------
# extracting fenced code from a markdown file

import re


def test_extract():
    a = Awk()

    @a.between(Awk.match(" *```"), Awk.match(" *```"))
    def printcode(self):
        if self.result is True: # between on and off
            self.print(self.line)

    a("inputs/fence.txt", output="result.txt")
    assert fc.cmp("outputs/extract.txt", "result.txt")
    os.remove("result.txt")