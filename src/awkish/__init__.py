"""
A python class that can be used to do line-by-line processing of files, inspired by awk.

## Install.

```
pip install awkish
```

## Examples.

To use awkish you

1. Create an instance of the `Awk` object.
2. Define conditions and actions
3. Run it on one or more files

This may be easiest explained with a set of examples:

### Print all lines

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()

# 2. define conditions and actions
@awk.when(True)
def doline(line):
    print(line)

# 3. run it on a file
awk('filename.txt')
```

The condition decorator `@awk.when(True)` indicates that the decorated action should be called for every line.

The action function `doline` is declared with a parameter `line` which is filled in with
the entire contents of the line each time it is called.

Finally, the awkish object is called with the name of the file to be processed. Output
(if any)
is sent to `stdout` by default, but if you want it redirected, you can add a named output parameter:
`awk('filename.txt', output='out.txt')`

This example could also be written as

```python
from awkish import Awk
awk = Awk()

awk.when(True)()

awk('filename.txt')
```

When the condition decorator is called as a normal function, the action defaults to
`lambda line:print(line)` much like awk itself.
This is the idiom we'll use below, when we can.

### Print Every 2nd Line

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()

# 2. define conditions and actions
awk.when(lambda nfr: nfr%2==0)()

# 3. run it on a file
awk('filename.txt')
```

The condition decorator `@awk.when(...)` will invoke the default decorated action
`lambda line:print(line)` every time the predicate
is true. Here the predicate `lambda nfr: nfr%2==0` is declared with a parameter `nfr`
which is filled in with the **n**umber of **f**ile **r**ecords that have been processed.

### Print lines longer than 80 characters

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()

# 2. define conditions and actions
awk.when(lambda line: len(line)>80)()

# 3. run it on a file
awk('filename.txt')
```

### Print the longest line

```python
from awkish import Awk

# globals to track line length
linelen = -1
longest_line = None

# 1. create the awk object
longest = Awk()

# 2. define conditions and actions

@longest.when(lambda line:len(line)>linelen)
def savelongest(line):
    global linelen, longest_line
    linelen = len(line)
    longest_line = line

@longest.end
def reportlongest():
    global linelen, longest_line
    print(f'The longest line is {linelen} characters long:')
    print(longest_line)

# 3. run it on a file
longest('filename.txt')
```

This example uses globals to keep track of the line and length. The decorator
`longest.end` will run the decorated function after the file has been
processed. If you pass multiple filenames to the awk object, the function(s) decorated
by `end` will run after each file. To run functions after all files, use the `endjob` decorator.

There are also `begin` and `beginjob` decorators.

### Print some fields of a CSV file.

```python
from awkish import Awk

# 1. create the awk object
awk = Awk(FS=Awk.CSV)

# 2. define conditions and actions
awk.when(True)(lambda f1, f3:print(f1+','+f3))

# 3. run it on a file
awk('filename.txt')
```

In this case the awk field seperator `FS` is set to `Awk.CSV` which is a function that
parses records according to RFC4180 (except that, since records/lines are parsed first, quoted fields can't include line breaks). Just using `FS=','` won't achieve this.

The lambda function is declared with two parameters `f1` and `f3` which are filled in
with the (string) values of the first and third fields in the record. These correspond
to `$1` and `$3` in awk proper (but `$` isn't a legal identifier character in python,
so `f` is used instead.)

### Print all lines which have some target text

```python
from awkish import Awk
awk = Awk(FS=Awk.CSV)

awk.find('John')()

awk('filename.txt')
```

The decorator `awk.find(pattern)` will look for the pattern in each line/record and return the index if it exists, and False otherwise.

If you want to print where
the pattern is found, then you could do this:

```python
from awkish import Awk
awk = Awk(FS=Awk.CSV)

awk.find('John')(lambda result: print('John found at position', result))
awk.find('John')()

awk('filename.txt')
```

This will print two lines for each find: the first one says where the pattern was
found (using the parameter `result`) and the second one prints the line. Actions are
executed in the order they are defined.

In this example, searching for John twice per line (which happens because the
`find` decorator is used twice) isn't exactly efficient, but awkish is really more
about convenience.

If you'd rather use a regular
expression, `awk.search(pattern)` will invoke `re.search(pattern, line)` for
each line/record in the file, and do the associated action (in this case, the default).

There is also a `match` decorator which invokes `re.match` instead.

The `result` parameter always contains the return value of the condition, when it
succeeds (that is, when it doesn't return `False` or `None`). This allows you to
pass information about the predicate to the action, and is particularly useful for
`find`, `search`, and `match` decorators.

## Command-Line Usage.

When implemented it will allow you to do the following:

1. Write the awk program as before, but leave out the call `awk(filename.txt)`, because
   the command line will provide the file name(s). Save your program in
   e.g `awkprog.py`
2. Type `python -m awkish awkprog.py filename1 filename2 ... --output=out.txt` at the command line.

When invoked as a module, `awkish` imports the first file containing the program, finds the `Awk` object, and then calls it on the file list following.

"""

__version__ = "0.1"  # first release

from .awk import Awk

