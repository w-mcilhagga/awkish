# -*- coding: utf-8 -*-
"""
awkish - Awk is a small class in pure python that does awk-like line processing.
"""

__version__ = "0.1"  # first release

import inspect
import re
import sys
from contextlib import redirect_stdout as redirect, contextmanager


def _argwrap(f):
    # works out arg names of f in order, then wraps it in a call using a
    # dict arg which has those names
    #
    # want to be clever and set up args that don't exist with their default
    # values, and to copy those values back to args. Use ProxyTypes or wrapt
    # proxies; however these don't support direct assignment as this can't
    # be overridden in python
    #
    # inspect.signature(f).parameters[name].default

    params = inspect.signature(f).parameters
    argnames = tuple(params)

    def wrapped(d):
        return f(*(d.get(name, params[name].default) for name in argnames))

    return wrapped


# CSV parsing regexes
escaped = r'(?:"(?:(?:(?:"")|[^"])*)")'
unescaped = r'(?:[^,"]*)'
field = f"({escaped}|{unescaped})"  # capturing
record = f"(?:^|,){field}"


class Awk:
    _csv_re = re.compile(record)

    @staticmethod
    def CSV(line, strict=True):
        """a field seperator function, which can be used as the FS parameter
        when creating a Awk object. This is **not** the same as setting FS to
        a comma.

        Args:
            line: a string to be interpreted as one line of a CSV file.
            strict: boolean to decide whether to raise an exception if the
                line doesn't conform to RFC4180

        Returns:
            a list of fields as strings. Escaped strings have their quotes
            removed and double quotes converted to single quotes.

        This mostly follows RFC4180 except that quoted fields cannot contain
        line breaks, as these are used by the file reader to break the file
        into lines.

        If the line does not conform to RFC4180, the function attempts to
        find fields anyway if strict is False; it raises a ValueError otherwise.

        Note that in the case of strict=False, to use as a FS in Awk it
        has to be wrapped in a lambda, e.g.

        ```
        awk = Awk(FS=lambda line: Awk.CSV(line, strict=False))
        ```
        Otherwise, it is enough to simply say `FS=Awk.CSV`

        Raises:
            ValueError when strict is True and line isn't RFC4180 compatible
        """

        fields_gaps = Awk._csv_re.split(line)
        # elements 0, 2, 4, ... should be ''
        # and elements 1, 3, 5, ... should be the fields
        # BUT any errors will cause the 0,2,4 to have some content.
        fields = fields_gaps[1::2]
        gaps = fields_gaps[2::2]
        if len("".join(gaps)) > 0 and strict:
            raise ValueError(f"Line \n{line}\nnot compatible with RFC4180")
        fields = [g + v for (g, v) in zip(gaps, fields)]
        return [f.strip('"').replace('""', '"') for f in fields]

    def __init__(self, FS=re.compile(" +"), RS=None):
        """creates an instance of an awk-like program object

        Args:
            FS: the field separator. If a character, each line is split
                using string.split(FS). If a regular expression object,
                each line is split using FS.split(string). If a callable,
                it is passed the line and returns a list of fields. The default is
                to remove multiple spaces.
            RS: the record separator, used as the newline parameter to an open
                call. Default is None. See open in the standard library for
                more details.

                Note that if RS is None, the line ends are stripped
                from each line (different behaviour to open).
        Returns:
            a callable Awk object. This can be used to process files by calling it. For
        example
        ```
        ma = Awk()
        # define actions
        ma(filename1, filename2, filename3)
        ```
        will create a Awk object and run it over the three files named in
        the call and dump any output to stdout. The parameters to the call are

        * `*filenames` - the names of the text files to process
        * `output` - (optiona) the name of the file to dump the program output
        * `mode` - (optional) when `output` is specified, the open mode (defaults
            to "wt")
        """
        self.FS = FS  # field separator
        self.RS = RS  # record separator, passed to open() as newline
        self.beginjob_calls = []
        self.endjob_calls = []
        self.begin_calls = []
        self.end_calls = []
        self.calls = []

    def beginjob(self, f):
        """decorator for functions to be called before any files
        are processed

        For example, if `ma` is a Awk object,
        ```
        @ma.beginjob
        def setup():
            global x
            x = {}
        ```
        then the setup function will be called at the start of processing.
        Multiple functions can be decorated by begin and will be executed in turn
        at the start of processing.
        Any such decorated function can take any of the following arguments:

        * `FS` - the file seperator used when the Awk object was created
        * `RS` - the record separator used when the Awk object was created
        * `nr` - the number of records read in the job, which be zero
           when the function is called.

        """
        self.beginjob_calls.append(_argwrap(f))

    def endjob(self, f):
        """decorator for functions to be called after all files
        are processed

        For example, if `ma` is a Awk object,
        ```
        @ma.endjob
        def cleanup():
            global x
            x = {}
        ```
        then the cleanup function will be called at the end of processing.
        Multiple functions can be decorated by end and will be executed in turn
        at the end of processing.
        Any such decorated function can take thes same arguments as `Awk.beginjob`.
        """

        self.endjob_calls.append(_argwrap(f))

    def begin(self, f):
        """decorator for functions to be called before each file
        being processed

        For example, if `ma` is a Awk object,
        ```
        @ma.begin
        def startfile():
            global x
            x = {}
        ```
        then the startfile function will be called before processing any file.
        Multiple functions can be decorated by beginfile and will be executed in turn
        before processing any file.
        Any such decorated function can take the same arguments as `Awk.beginjob` and:

        * `filename` - the name fo the file being processed
        * `nfr` - the number of records read in the file, which will be zero
           when the function is called.

        """
        self.begin_calls.append(_argwrap(f))

    def end(self, f):
        """decorator for functions to be called after each file
        being processed

        For example, if `ma` is a Awk object,
        ```
        @ma.end
        def afterfile():
            global x
            x = {}
        ```
        then the afterfile function will be after processing each file.
        Multiple functions can be decorated by endfile and will be executed in turn
        after processing any file.
        Any such decorated function can use the same arguments as `Awk.begin`.
        """
        self.end_calls.append(_argwrap(f))

    def _condition_decorator(self, condition):
        # internal to make the decorator

        def condition_decorator(f=lambda line: print(line)):
            # introspect f to see what to pass it.
            self.calls.append([_argwrap(condition), _argwrap(f)])
            return f

        return condition_decorator

    def when(self, condition):
        """decorator for functions to be called during file processing.

        Args:
            condition: a boolean or callable which determines whether the current line
                should be passed to the decorated function. Anything value
                returned other than False or None is equivalent to True.
                condition may be True, in which case all lines are processed.

        For example, if `ma` is a Awk object,
        ```
        @ma.when(lambda line:line[0]=='$')
        def doline(line):
            print(line)
        ```

        then the `doline` action will be triggered for every line starting with $,
        and print it.
        
        The default action is `lambda line:print(line)` so the above could be
        simplified to
        ```
        ma.when(lambda line:line[0]=='$')()
        ```

        If the condition is `True`, as here:

        ```
        @ma.when(True)
        def doline(line):
            print(line)
        ```
        then the decorated action `doline` will be called for every line.

        Both the condition
        passed to `when` and the decorated function can use the same parameters
        passed to `Awk.begin` and in addition:

        * `line` - the entire line being processed
        * `fields` - a list of fields parsed from the line
        * `f0` - synonym for `line`, like awk's $0 variable
        * `f1`, `f2`, ... - the individual parsed fields (which are None if
           they don't exist) like awk's $1, $2, ... variables
        * `nf` - the number of fields, equal to `len(fields)`
        * `result` - the result of the condition passed to `when`


        """
        if type(condition) is bool:
            condition = lambda: condition

        return self._condition_decorator(condition)

    def find(self, string):
        return self._condition_decorator(
            lambda line: idx if (idx != line.find(string)) != -1 else False
        )

    def match(self, patt):
        """decorator for functions to be called during file processing.

        Args:
            patt: the regular expression pattern to match to the start of
                the current line

        For example, if ma is a Awk object,
        ```
        @ma.match(r'[A-Z]')
        def doline(line):
            print(line)
        ```

        then `doline` will be triggered and print every line starting with a capital letter.
        `match(patt)` is equivalent to `when(lambda line:re.match(patt, line))`

        The decorated function can use the same parameters as `Awk.when`

        """
        rex = re.compile(patt)
        return self._condition_decorator(lambda line: rex.match(line))

    def search(self, patt):
        """decorator for functions to be called during file processing.

        Args:
            patt: the regular expression pattern to match to anywhere in
                the current line

        For example, if ma is a Awk object,
        ```
        @ma.search(r'[A-Z]')
        def doline(line):
            print(line)
        ```

        then `doline` will be triggered for every line containing a capital letter.
        `search(patt)` is equivalent to `when(lambda line:re.search(patt, line))`

        The decorated function can use the same parameters as `Awk.when`

        """
        rex = re.compile(patt)
        return self._condition_decorator(lambda line: rex.search(line))

    def __call__(self, *filenames, output=None, mode="wt"):
        # run the awk over all the files
        @contextmanager
        def file_or_stdout(f):
            # __enter__
            outfile = sys.stdout if f is None else open(f, mode)
            yield outfile
            # __exit__
            if f is not None:
                outfile.close()

        args = {
            "FS": self.FS,
            "RS": self.RS,
            "nr": 0,
        }
        with file_or_stdout(output) as f:
            with redirect(f):
                # run the begin code
                for action in self.beginjob_calls:
                    action(args)
                # process the files
                for fname in filenames:
                    args["nr"] = self._processfile(fname, {**args})
                # run the end code
                for action in self.endjob_calls:
                    action(args)

    def _processfile(self, fname, proc_args):
        # args has line, fields f0, f1, ... nr, fnr, filename, self
        # f0 is the same as the line
        # f1, f2, .. are the fields fields[0], fields[1], ...
        # f1, ... are not guaranteed to exist so you have to give default
        # values in an action or condition (otherwise you get inspect._empty)
        proc_args = {**proc_args, "filename": fname}
        for action in self.begin_calls:
            action(proc_args)
        with open(fname, newline=self.RS) as file:
            proc_args["fnr"] = 0
            for item in file:
                proc_args["fnr"] += 1
                proc_args["nr"] += 1
                # copy args for this loop
                args = {**proc_args}
                # setup args['line']
                if self.RS in [None, ""]:
                    item = re.sub(r"(\r\n|\n)$", "", item)
                else:
                    item = item.replace(self.RS, "")
                args["line"] = args["f0"] = item
                # parse the fields
                if callable(self.FS):
                    fields = self.FS(item)
                elif type(self.FS) is re.Pattern:
                    # empty separators are a nuisance
                    if self.FS.pattern == "":
                        fields = [*item]
                    else:
                        fields = self.FS.split(item)
                elif self.FS == "":
                    # empty separators are a nuisance
                    fields = [*item]
                else:
                    fields = item.split(self.FS)
                args["fields"] = fields
                args["nf"] = len(fields)
                for i, value in enumerate(fields):
                    args[f"f{i+1}"] = fields[i]
                # run all the calls
                for condition, action in self.calls:
                    result = condition(args)
                    if result not in [None, False]:
                        action({**args, "result": result})
        for action in self.end_calls:
            action(proc_args)
        # return the only value to persist between calls
        return proc_args["nr"]
