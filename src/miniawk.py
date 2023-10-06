# -*- coding: utf-8 -*-
"""
miniawk - a small class in pure python that does awk-like line processing.
"""

__version__ = "0.1"  # first release

import inspect
import re


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


class MiniAwk:

    _csv_re = re.compile(record)

    @staticmethod
    def CSV(line):
        """a field seperator function, which can be used as the FS parameter
        when creating a MiniAwk object. This is **not** the same as setting FS to
        a comma.
        
        Args:
            line: a string to be interpreted as one line of a CSV file.
            
        Returns:
            a list of fields as strings. Escaped strings have their quotes
            removed and double quotes converted to single quotes.
            
        This mostly follows RFC4180 except that quoted fields cannot contain 
        line breaks, as these are used by the file reader to break the file 
        into lines. 
        
        If the line does not conform to RFC4180, the function attempts to 
        find fields anyway, though it is not always successful.
        """

        fields_gaps = MiniAwk._csv_re.split(line)
        # elements 0, 2, 4, ... should be ''
        # and elements 1, 3, 5, ... should be the fields
        # BUT any errors will cause the 0,2,4 to have some content.
        fields = fields_gaps[1::2]
        gaps = fields_gaps[2::2]
        # print(*zip(gaps, fields))
        # gaps should be same length as fields
        fields = [g + v for (g, v) in zip(gaps, fields)]
        return [f.strip('"').replace('""', '"') for f in fields]

    def __init__(self, FS=re.compile(' +'), RS=None):
        """creates an instance of an awk-like program object
        
        Args:
            FS: the field separator. If a character, each line is split 
                using string.split(FS). If a regular expression object, 
                each line is split using FS.split(string). If a callable, 
                it is called to split the line. Default is to remove multiple
                spaces.
            RS: the record separator, used as the newline parameter to an open
                call. Default is None. See open in the standard library for 
                more details.
                
                Note that if RS is None, the line ends are stripped 
                from each line (different behaviour to open).
        Returns:
            a callable MiniAwk object
            
        A MiniAwk object can be used to process files by calling it. For
        example
        ```
        ma = MiniAwk()
        # define actions
        ma(filename1, filename2, filename3)
        ```
        will create a MiniAwk object and run it over the three files named in
        the call.
        """
        self.FS = FS  # field separator
        self.RS = RS  # record separator, passed to open() as newline
        self.begin_calls = []
        self.end_calls = []
        self.beginfile_calls = []
        self.endfile_calls = []
        self.calls = []

    def begin(self, f):
        """decorator for functions to be called before any files
        are processed
        
        For example, if ma is a MiniAwk object, 
        ```
        @ma.begin
        def setup():
            global x
            x = {}
        ```
        then the setup function will be called at the start of processing. 
        Multiple functions can be decorated by begin and will be executed in turn
        at the start of processing.
        Any such decorated function can take arguments called FS, RS, and nr, although it
        can't currently change them.
        """
        self.begin_calls.append(_argwrap(f))

    def end(self, f):
        """decorator for functions to be called after all files
        are processed
        
        For example, if ma is a MiniAwk object, 
        ```
        @ma.end
        def cleanup():
            global x
            x = {}
        ```
        then the cleanup function will be called at the end of processing. 
        Multiple functions can be decorated by end and will be executed in turn
        at the end of processing.
        Any such decorated function can take arguments called FS, RS, and nr, although it
        can't currently change them.
        """
        
        self.end_calls.append(_argwrap(f))

    def beginfile(self, f):
        """decorator for functions to be called before each file
        being processed
        
        For example, if ma is a MiniAwk object, 
        ```
        @ma.beginfile
        def startfile():
            global x
            x = {}
        ```
        then the startfile function will be called before processing any file. 
        Multiple functions can be decorated by beginfile and will be executed in turn
        before processing any file.
        Any such decorated function can take arguments called FS, RS, nr, and filename,
        although it
        can't currently change them.
        """
        self.beginfile_calls.append(_argwrap(f))

    def endfile(self, f):
        """decorator for functions to be called after each file
        being processed
        
        For example, if ma is a MiniAwk object, 
        ```
        @ma.endfile
        def afterfile():
            global x
            x = {}
        ```
        then the afterfile function will be after processing each file. 
        Multiple functions can be decorated by endfile and will be executed in turn
        after processing any file.
        Any such decorated function can take arguments called FS, RS, nr, and filename,
        although it can't currently change them.
        """
        self.endfile_calls.append(_argwrap(f))

    def on(self, condition=lambda: True):
        """decorator for functions to be called during file processing.
        
        Args:
            condition: a callable which determines whether the current line
                should be passed to the decorated function. Anything value 
                returned other than False or None is equivalent to True. The default is
                `lambda: True`
                
        For example, if ma is a MiniAwk object, 
        ```
        @ma.on(lambda line:line[0]=='$')
        def doline(line):
            print(line)
        ```
        
        then `doline` will be triggered for every line starting with $, 
        and print it. Both the condition
        passed to `on` and the decorated function can use parameters 
        FS, RS, nr, fnr, filename, line, fields, f0, f1, ..., and result.
        
        """
        def conditional_decorator(f):
            # introspect f to see what to pass it.
            self.calls.append([_argwrap(condition), _argwrap(f)])
            return f

        return conditional_decorator

    def onmatch(self, patt):
        """decorator for functions to be called during file processing.
        
        Args:
            patt: the regular expression pattern to match to the start of
                the current line
                
        For example, if ma is a MiniAwk object, 
        ```
        @ma.onmatch(r'[A-Z]')
        def doline(line):
            print(line)
        ```
        
        then `doline` will be triggered and print every line starting with a capital letter. 
        The decorated function can use parameters 
        FS, RS, nr, fnr, filename, line, fields, f0, f1, ..., and result.
        
        `onmatch(patt)` is equivalent to `on(lambda line:re.match(patt, line))`
        
        """
        rex = re.compile(patt)

        def conditional_decorator(f):
            # introspect f to see what to pass it.
            self.calls.append(
                [_argwrap(lambda line: rex.match(line)), _argwrap(f)]
            )
            return f

        return conditional_decorator

    def onsearch(self, patt):
        """decorator for functions to be called during file processing.
        
        Args:
            patt: the regular expression pattern to match to anywhere in
                the current line
                
        For example, if ma is a MiniAwk object, 
        ```
        @ma.onmatch(r'[A-Z]')
        def doline(line):
            print(line)
        ```
        
        then `doline` will be triggered for every line containing a capital letter. 
        The decorated function can use parameters 
        FS, RS, nr, fnr, filename, line, fields, f0, f1, ..., and result.
        
        `onsearch(patt)` is equivalent to `on(lambda line:re.search(patt, line))`
        
        """
        rex = re.compile(patt)

        def conditional_decorator(f):
            # introspect f to see what to pass it.
            self.calls.append(
                [_argwrap(lambda line: rex.search(line)), _argwrap(f)]
            )
            return f

        return conditional_decorator

    def __call__(self, *filenames):
        # run the begin code
        args = {
            "FS": self.FS,
            "RS": self.RS,
            "nr": 0,
        }
        for action in self.begin_calls:
            action(args)
        # process the files
        for fname in filenames:
            args["nr"] = self._processfile(fname, {**args})
        # run the end code
        for action in self.end_calls:
            action(args)

    def _processfile(self, fname, proc_args):
        # args has line, fields f0, f1, ... nr, fnr, filename, self
        # f0 is the same as the line
        # f1, f2, .. are the fields fields[0], fields[1], ...
        # f1, ... are not guaranteed to exist so you have to give default
        # values in an action or condition (otherwise you get inspect._empty)
        proc_args = {**proc_args, "filename": fname}
        for action in self.beginfile_calls:
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
        for action in self.endfile_calls:
            action(proc_args)
        # return the only value to persist between calls
        return proc_args["nr"]



