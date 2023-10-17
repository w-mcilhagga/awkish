# HANDY "ONE-LINE" SCRIPTS FOR AWKISH

These are one-liners in awk, but awkish is a bit more verbose.
All these examples should be preceded by

```python
from awkish import Awk()
```

Originally compiled for awk by Eric Pement - eric [at] pement.org

## FILE SPACING:

**awkish doesn't have ORS so we need to work around this**

### double space a file

```python
a = Awk()
a.when(True)(lambda line:print(line)
```

This works because each line in the file has the line end (\n or \r\n) on it.

### double space a file which already has blank lines in it.

Output file should contain no more than one blank line between lines of text.

```python
a = Awk()
a.when(lambda nf:nf>0)(lambda line:print(line)
```

### triple space a file

```python
a = Awk()
a.when(True)(lambda line:print(line+'\n')
```

## NUMBERING AND CALCULATIONS:

### precede each line by its line number FOR THAT FILE (left alignment).

Using a tab (\t) instead of space will preserve margins.

```python
a = Awk()
a.when(True)(lambda fnr, line: print(fnr+'\t'+line, end='')
```

### precede each line by its line number FOR ALL FILES TOGETHER, with tab.

```python
a = Awk()
a.when(True)(lambda nr, line: print(nr+'\t'+line, end='')
a(file1, file2, ...)
```

### number each line of file, but only print numbers if line is not blank

```python
a = Awk()
@a.when(True)
def numberlines(fnr, nf, line):
    if nf>0:
        print(fnr+'\t'+line, end='')
    else:
        print('\t'+line, end='')
```

### count lines (emulates "wc -l")

```python
a = Awk()
a.end(lambda fnr: print(fnr))
```

### print the sums of the fields of every line

```python
a = Awk()
a.when(True)(lambda fields:print(sum(map(float, fields))))
```

### print the total number of fields ("words") in all lines

```python
a = Awk()
a.begin(lambda self:self.tnf=0)
a.when(True)(lambda self, nf:self.tnf+=nf)
a.end(lambda self:print(self.tnf)
```

### print the total number of lines that contain "Beth"

```python
a = Awk()
a.begin(lambda self:self.total=0)
a.when(Awk.find("Beth"))(lambda self:self.total+=1)
a.end(lambda self:print(self.total)
```

### print the largest first field and the line that contains it

Intended for finding the longest string in field #1

```python
a = Awk()
a.begin(lambda self:self.max=0)
@a.when(lambda self, f1:len(f1)>self.max)
def save(self, line, f1):
    self.max = len(f1)
a.end(lambda self:print(self.max, self.line)
```

### print the number of fields in each line, followed by the line

```python
a = Awk()
a.when(True)(lambda nf,line: print(str(nf)+':\n'+line))
```

### print the last field of each line

```python
a = Awk()
a.when(True)(lambda fields: print(fields[-1]))
```

### print the last field of the last line

awk '{ field = $NF }; END{ print field }'

### print every line with more than 4 fields

```python
a = Awk()
a.when(lambda nf: nf>4)()
```

### print every line where the value of the last field is > 4

```python
a = Awk()
a.when(lambda f4='': nf>4)()
```

## TEXT CONVERSION AND SUBSTITUTION:

### delete leading whitespace (spaces, tabs) from front of each line

aligns all text flush left

awk '{sub(/^[ \t]+/, "")};1'

### delete trailing whitespace (spaces, tabs) from end of each line

awk '{sub(/[ \t]+$/, "")};1'

### delete BOTH leading and trailing whitespace from each line

awk '{gsub(/^[ \t]+|[ \t]+$/,"")};1'
awk '{$1=$1};1' # also removes extra space between fields

### insert 5 blank spaces at beginning of each line (make page offset)

awk '{sub(/^/, " ")};1'

### align all text flush right on a 79-column width

awk '{printf "%79s\n", $0}' file\*

### center all text on a 79-character width

awk '{l=length();s=int((79-l)/2); printf "%"(s+l)"s\n",$0}' file\*

### substitute (find and replace) "foo" with "bar" on each line

```python
a = Awk()
@a.when(True)
def rep(line, findstr, repstring):
    print(line.replace(findstr, repstring))
a(filename, findstr='foo', repstring='bar')
```

### substitute "foo" with "bar" ONLY for lines which contain "baz"

the problem here is that the line is read-only in awkish whereas it's
a global in awk, so it can be altered.

```python
a = Awk()
@a.when(Awk.find('baz'))
def rep(self, line, findstr, repstring):
    self.line = line.replace(findstr, repstring))
a.when(True)(lambda self:self.print(self.line))
a(filename, findstr='foo', repstring='bar')
```

In this case, we store the substitution in line -- doesn't work, cos line
is not always defined.

### substitute "foo" with "bar" EXCEPT for lines which contain "baz"

awk '!/baz/{gsub(/foo/, "bar")}; 1'

### change "scarlet" or "ruby" or "puce" to "red"

awk '{gsub(/scarlet|ruby|puce/, "red")}; 1'

### reverse order of lines (emulates "tac")

awk '{a[i++]=$0} END {for (j=i-1; j>=0;) print a[j--] }' file\*

### if a line ends with a backslash, append the next line to it

(fails if there are multiple lines ending with backslash...)

awk '/\\$/ {sub(/\\$/,""); getline t; print $0 t; next}; 1' file\*

### print and sort the login names of all users

awk -F ":" '{print $1 | "sort" }' /etc/passwd

### print the first 2 fields, in opposite order, of every line

```python
a = Awk()
a.when(True)(lambda f1,f2: print(f2, f1, sep=','))
```

### print every line, deleting the second field of that line

```python
a = Awk()
@a.when(True)
def printline(self, fields):
    fields[1]=''
    self.print(*fields)
```

### print in reverse order the fields of every line

awk '{for (i=NF; i>0; i--) printf("%s ",$i);print ""}' file

### concatenate every 5 lines of input

using a comma separator between fields

awk 'ORS=NR%5?",":"\n"' file

## SELECTIVE PRINTING OF CERTAIN LINES:

### print first 10 lines of file (emulates behavior of "head")

```python
a = Awk()
a.when(lambda nr:nr<11)()
```

### print first line of file (emulates "head -1")

```python
a = Awk()
a.when(lambda nr:nr<2)()
```

Not very efficient, because no early exit.

### print the last 2 lines of a file (emulates "tail -2")

```python
a = Awk()
@a.begin
def b(self):
    self.lines = ('',)
@a.when(True)
def update(self, line):
    self.lines = self.lines[-1], line
a.end(lambda self:print(self.lines, sep='\n', end='')
```

### print the last line of a file (emulates "tail -1")

```python
a = Awk()
@a.when(True)
def update(self, line):
    self.line = line
a.end(lambda self:self.print(self.line)
```

### print only lines which match regular expression (emulates "grep")

awk '/regex/'

### print only lines which do NOT match regex (emulates "grep -v")

awk '!/regex/'

### print any line where field #5 is equal to "abc123"

```python
a = Awk()
a.when(lambda f5='':f5=="abc123")()
```

### print only those lines where field #5 is NOT equal to "abc123"

This will also print lines which have less than 5 fields.

```python
a = Awk()
a.when(lambda f5='':f5!="abc123")()
```

### matching a field against a regular expression

awk '$7 ~ /^[a-f]/' # print line if field #7 matches regex
awk '$7 !~ /^[a-f]/' # print line if field #7 does NOT match regex

### print the line immediately before a regex, but not the line containing the regex

awk '/regex/{print x};{x=$0}'
awk '/regex/{print (NR==1 ? "match on line 1" : x)};{x=$0}'

### print the line immediately after a regex, but not the line containing the regex

awk '/regex/{getline;print}'

### grep for AAA and BBB and CCC (in any order on the same line)

awk '/AAA/ && /BBB/ && /CCC/'

### grep for AAA and BBB and CCC (in that order)

awk '/AAA.*BBB.*CCC/'

### print only lines of 65 characters or longer

```python
a = Awk()
a.when(lambda length:length>65)()
```

### print section of file from regular expression to end of file

awk '/regex/,0'
awk '/regex/,EOF'

### print section of file based on line numbers (lines 8-12, inclusive)

```python
a = Awk()
a.when(lambda nr:nr>=8 and nr<=12)()
```

or

```python
a = Awk()
a.between(lambda nr:nr==8, lambda nr: nr==12)()
```

### print line number 52

awk 'NR==52'
awk 'NR==52 {print;exit}' # more efficient on large files

### print section of file between two regular expressions (inclusive)

awk '/Iowa/,/Montana/' # case sensitive

## SELECTIVE DELETION OF CERTAIN LINES:

### delete ALL blank lines from a file (same as "grep '.' ")

awk NF
awk '/./'

### remove duplicate, consecutive lines (emulates "uniq")

awk 'a !~ $0; {a=$0}'

### remove duplicate, nonconsecutive lines

awk '!a[$0]++' # most concise script
awk '!($0 in a){a[$0];print}' # most efficient script
