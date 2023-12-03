# awkish

A python class that can be used to do line-by-line processing of files, inspired by awk.
Programs written with awkish are typically more verbose than awk files, but I liked how awk was designed and wanted to replicate it in python.

## Install.

Use pip when it's put there.

## Examples.

To use awkish you

1. Create an instance of the `Awk` object.
2. Define conditions and associated actions
3. Run it on one or more files

This may be easiest explained with a set of examples:

### Print all lines

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()

# 2. define conditions and actions
@awk.all
def doline(self):
    print(self.line, end=self.line_end)

# 3. run it on a file
awk('filename.txt')
```

The `awk.all` decorator makes the decorated action run on each line/record of input.
The action function `doline` is declared with an optional parameter `self` which will be set to the awk object when called. The awk object has various
attributes set when called; one is `line` which is the current line excluding endline
characters. (The endline characters are in `self.line_end`)

To run the program, the awkish object is called with the name of the file to be processed. Output
is sent to `stdout` by default, but if you want it redirected, you can add a named output parameter, for example
`awk('filename.txt', output='out.txt')`

The above example could also be written as

```python
from awkish import Awk
awk = Awk()
awk.all()
awk('filename.txt')
```

When an awk decorator is called as a normal function, the action defaults to
`lambda self:self.print(self.line, end=self.line_end)` much like awk itself.

### Print Every 2nd Line

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()

# 2. define conditions and actions
awk.when(lambda self: self.nfr%2==0)()

# 3. run it on a file
awk('filename.txt')
```

The condition decorator `awk.when(...)`, used in a normal call here, will invoke the default action every time the predicate
is true. Here the predicate `lambda self: self.nfr%2==0` uses the attribute `nfr`
which is filled in with the **n**umber of **f**ile **r**ecords that have been processed.

See the documentation for the awk object attributes available to the actions and conditions.

### Print lines longer than 80 characters

```python
from awkish import Awk

awk = Awk()
awk.when(lambda self: self.length>80)()
awk('filename.txt')
```

The `length` attribute is just `len(self.line)`

### Print the longest line

```python
from awkish import Awk

# 1. create the awk object
awk = Awk()


# 2. define conditions and actions
@awk.begin
def startup(self);
    self.linelen = -1
    self.longest_line = None

@awk.when(lambda self: self.length > linelen)
def savelongest(self):
    self.linelen = self.length
    self.longest_line = self.line

@awk.end
def reportlongest(self):
    print(f'The longest line is {self.linelen} characters long:')
    print(self.longest_line)

# 3. run it on a file
awk('filename.txt')
```

The decorator `awk.begin` initializes some attributes of the awk object. The decorator
`awk.end` will print those attributes after the file has been processed.

**Note:** If you pass multiple filenames to the awk object, the action(s) decorated
by `begin` and `end` will run before and after each file. To run actions before any files have been processed, use the `beginjob` decorator. To run actions after all files have been processed, use the `endjob` decorator.

### Print some fields of a CSV file.

```python
from awkish import Awk

awk = Awk(FS=Awk.CSV, OFS=',', ORS='\n')
awk.all(lambda self: self.print(self.f1,self.f3))
awk('filename.csv')
```

In this case the awk field seperator `FS` is set to `Awk.CSV` which
parses records according to RFC4180 (except that, since records/lines are parsed first, quoted fields can't include line breaks). Just using `FS=','` won't achieve this. `OFS` and `ORS` are the output field and record separators.

The lambda function uses two attributes `f1` and `f3` which are filled in
with the (string) values of the first and third fields in the record. These correspond
to `$1` and `$3` in awk proper (but `$` isn't a legal identifier character in python,
so `f` is used instead.)

Note that Awk objects will return `None` for fields that don't exist.

### Print all lines which have some target text

```python
from awkish import Awk

awk = Awk(FS=Awk.CSV)
awk.when(Awk.find('John'))()
awk('filename.txt')
```

The static method `Awk.find(pattern)` returns a condition which looks for the pattern in each line/record and returns the pattern's index if it is in the line, and False otherwise.

If you want to print where the pattern is found, then you could do this:

```python
from awkish import Awk

awk = Awk(FS=Awk.CSV)

awk.when(Awk.find('John'))(
    lambda self: print('John found at position', self.result)
)
awk.when(Awk.find('John'))()

awk('filename.txt')
```

This will print two lines for each find: the first one says where the pattern was
found (using the parameter `result`) and the second one prints the line. Actions are
executed in the order they are defined.

If you'd rather use a regular
expression, `Awk.search(pattern)` will invoke `re.search(pattern, line)` for
each line/record in the file, and do the associated action (in this case, the default).

There is also an `Awk.match` static method which invokes `re.match` on the current line.

The `result` parameter always contains the return value of the condition, when it
succeeds (that is, when it doesn't return `False` or `None`). This allows you to
pass information about the predicate to the action, and is particularly useful for
`find`, `search`, and `match` decorators.

## Command-Line Usage.

`awkish` can be invoked from the command line.

```
python -m awkish path/to/awk_program.py file1 file2 ... -output=outfile
```

1. Write the awk program as before, but leave out the call `awk(filename.txt)` to do the processing,
   because the command line will provide the file name(s). Save your program in
   e.g `awkprog.py`
2. Type `python -m awkish path/to/awkprog.py filename1 filename2 ... --output=out.txt` at the command line,
   or whatever is needed to invoke python in your environment.

When run as a module, `awkish`

1. imports the first file containing the program and finds the `Awk` object defined therein
2. Calls it on the file list following. If no outfile is given, it prints any output
   to the command line.
