import argparse
import ast
import difflib
import re
import sys
from configparser import ConfigParser
from pathlib import Path
from textwrap import indent

import numpydoc.docscrape as nds
from numpydoc.docscrape import Parameter

from velin.examples_section_utils import reformat_example_lines


def f(a, b, *args, **kwargs):
    """
    Parameters
    ----------
    a: int
        its a
    u : int
        its b
    args : stuff
        var
    kwargs : stuff
        kwargs

    Returns
    -------
    nothing: None

    See Also
    --------
    a, b, c

    """


def g(a, b):
    """
    Parameters
    ----------
    a : int
        its a
    b : int
        its b
    args : stuff
        var
    kwargs : stuff
        kwargs
    Returns
    -------
    nothing: None

    See Also
    --------
    a, b, c

    """


class NodeVisitor(ast.NodeVisitor):
    def __init__(self, config):
        self.config = config
        self.items = []
        self.stack = []

    def visit(self, node):
        if type(node) in (ast.ClassDef, ast.FunctionDef):
            self.stack.append(node.name)
            # print(self.stack)
            oname = ".".join(self.stack)
            if oname in self.config["skip"]:
                print("SKIPPING", oname)
                self.stack.pop()
                return
            super().visit(node)
            self.stack.pop()
        elif type(node) in (
            ast.Load,
            ast.Name,
            ast.Call,
            ast.Compare,
            ast.Attribute,
            ast.Expr,
            ast.arguments,
            ast.Import,
            ast.alias,
            ast.Constant,
            ast.Store,
            ast.Assign,
            ast.arg,
        ):
            super().visit(node)
        else:
            # print(type(node))
            super().visit(node)

    def visit_FunctionDef(self, node):
        # we can collect function args, and _could_ check the Parameter section.
        # for nn in node.args.args:
        #    nnn = nn.arg
        # for k in [l for l in dir(node) if not l.startswith('_')]:
        #    sub = getattr(node, k)
        #    print(k, sub)
        #    for u in [l for l in dir(sub) if not l.startswith('_')]:
        #        ss = getattr(sub, u)
        #        print('    ', u, ss)

        # node.args.kwarg # single object
        # node.args.vararg # object
        # node.args.ks_defaults #list
        # print(node.returns)
        # node.args.defaults +

        meta = {
            "simple": [
                arg
                for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            ],
            "varargs": None,
            "varkwargs": None,
        }
        if node.args.kwarg:
            meta["varkwargs"] = node.args.kwarg
            dir(node.args.kwarg)
        if node.args.vararg:
            meta["varargs"] = node.args.vararg
        # print(arg.arg)
        #    for k in [l for l in dir(arg) if not l.startswith('_')]:
        #        sub = getattr(arg, k)
        #        print('    ', k, sub)

        self.items.append((node, meta, ".".join(self.stack)))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # we can collect function args, and _could_ check the Parameter section.
        # for nn in node.args.args:
        #    nnn = nn.arg

        # self.items.append((node, None))
        self.generic_visit(node)


BLACK_REFORMAT = True


class NumpyDocString(nds.NumpyDocString):
    """
    subclass a littel bit more lenient on parsing
    """

    aliases = {
        "Parameters": (
            "options",
            "parameter",
            "parameters",
            "paramters",
            "parmeters",
            "paramerters",
            "arguments",
            "args",
        ),
        "Attributes": ("properties",),
        "Yields": ("signals",),
    }

    def normalize(self):
        """
        Apply a bunch of heuristic that try to normalise the data.
        """
        if params := self["Parameters"]:
            for i, p in enumerate(params):
                if not p.type and (":" in p.name) and not p.name.endswith(":"):
                    if p.name.startswith(".."):
                        continue
                    if re.match(":\w+:`", p.name):
                        print("may have a directive", p.name)
                    try:
                        name, type_ = (
                            _.strip() for _ in p.name.split(": ", maxsplit=1)
                        )
                    except Exception as e:
                        raise type(e)(p.name)
                    params[i] = nds.Parameter(name, type_, p[2])

    def parse_examples(self, lines, indent=4):
        # this is bad practice be we do want normalisation here for now
        # to  check that parse->format->parse is idempotent.
        # this can be done if we had a separate "normalize" step.
        global BLACK_REFORMAT
        if BLACK_REFORMAT:
            try:
                lines = reformat_example_lines(lines, indent=indent)
            except Exception:
                print("black failed")
                print("\n".join(lines))
                raise

        return lines

    def to_json(self):

        res = {k: v for (k, v) in self.__dict__.items() if ((k not in {"_doc"}) and v)}
        res["_parsed_data"] = {k: v for (k, v) in res["_parsed_data"].items() if v}

        return res

    @classmethod
    def from_json(cls, obj):
        nds = cls("")
        nds.__dict__.update(obj)
        # print(obj['_parsed_data'].keys())
        nds._parsed_data["Parameters"] = [
            Parameter(a, b, c) for (a, b, c) in nds._parsed_data.get("Parameters", [])
        ]

        for it in (
            "Returns",
            "Yields",
            "Extended Summary",
            "Receives",
            "Other Parameters",
            "Raises",
            "Warns",
            "Warnings",
            "See Also",
            "Notes",
            "References",
            "Examples",
            "Attributes",
            "Methods",
        ):
            if it not in nds._parsed_data:
                nds._parsed_data[it] = []
        for it in ("index",):
            if it not in nds._parsed_data:
                nds._parsed_data[it] = {}
        return nds

    def __init__(self, *args, **kwargs):
        self.ordered_sections = []
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in ["Extended Summary", "Summary"]:
            value = [d.rstrip() for d in value]

        if key in ("Examples"):
            value = self.parse_examples(value)
        super().__setitem__(key, value)
        assert key not in self.ordered_sections
        self.ordered_sections.append(key)

    def _guess_header(self, header):
        if header in self.sections:
            return header
        # handle missing trailing `s`, and trailing `:`
        for s in self.sections:
            if s.lower().startswith(header.rstrip(":").lower()):
                return s
        for k, v in self.aliases.items():
            if header.lower() in v:
                return k
        raise ValueError("Cound not find match for section:", header)

    def _read_sections(self):
        for name, data in super()._read_sections():
            name = self._guess_header(name)
            yield name, data

    def _parse_param_list(self, *args, **kwargs):
        """
        Normalize parameters
        """
        parms = super()._parse_param_list(*args, **kwargs)
        out = []
        for name, type_, desc in parms:
            out.append(
                nds.Parameter(name.strip(), type_.strip(), [d.rstrip() for d in desc])
            )
        return out


def w(orig):
    """Util function that shows whitespace as `·`."""
    lines = []
    for line in orig:
        if line[0] in "+-":
            # ll.append(l.replace(' ', '⎵'))
            lines.append(line.replace(" ", "·"))

        else:
            lines.append(line)
    processed_lines = []
    for line in lines:
        if line.endswith("\n"):
            processed_lines.append(line[:-1])
        else:
            processed_lines.append(line[:])
    return processed_lines


class Config:
    """

    Here are some of the config options

    - F100: Items spacing in Return/Raise/Yield/Parameters/See Also
        - A(auto) - spaces if some sections have blank lines. (default)
        - B(compact) - no spaces between items, ever.
        - C(spaced)  - spaces between items, always

    """

    _compact_param = True
    _space_in_see_also_title = False
    _space_in_notes_title = False
    _run_fixers = True

    def __init__(self, conf):
        self._conf = conf

    def __getattr__(self, key):
        if key in self._conf:
            return self._conf[key]
        else:
            return getattr(type(self), "_" + key)


class SectionFormatter:
    """
    Render section of the docs, based on some configuration. Not having
    configuration is great, but everybody has their pet peevs, and I'm hpping we
    can progressively convince them to adopt a standard.
    """

    def __init__(self, *, conf):
        assert isinstance(conf, Config)
        self.config = conf

    @classmethod
    def format_Signature(self, s, compact):
        return s + "\n"

    @classmethod
    def format_Summary(self, s, compact):
        if len(s) == 1 and not s[0].strip():
            return ""
        return "\n".join(s) + "\n"

    @classmethod
    def format_Extended_Summary(self, es, compact):
        return "\n".join(es) + "\n"

    def _format_ps(self, name, ps, compact):
        res, try_other = self._format_ps_pref(name, ps, compact=True)
        if not try_other or self.config.compact_param:
            return res
        return self._format_ps_pref(name, ps, compact=False)[0]

    def _format_ps_pref(self, name, ps, *, compact):
        try_other = False
        out = name + "\n"
        out += "-" * len(name) + "\n"
        for i, p in enumerate(ps):
            if (not compact) and i:
                out += "\n"
            if p.type:
                out += f"""{p.name.strip()} : {p.type.strip()}\n"""
            else:
                out += f"""{p.name.strip()}\n"""
            if p.desc:
                if any([line.strip() == "" for line in p.desc]):
                    try_other = True

                out += indent("\n".join(p.desc), "    ")
                out += "\n"
        return out, try_other

    def format_Parameters(self, ps, compact):
        return self._format_ps("Parameters", ps, compact)

    def format_Methods(self, ps, compact):
        return self._format_ps("Methods", ps, compact)

    def format_Other_Parameters(self, ps, compact):
        return self._format_ps("Other Parameters", ps, compact)

    def format_See_Also(self, sas, compact):

        res = self.format_See_Also_impl(sas, True, force_compact=compact)
        if res is not None:
            return res
        return self.format_See_Also_impl(sas, False, force_compact=compact)

    def format_See_Also_impl(self, sas, compact, force_compact, *varargs, **varkwargs):
        """
        Format a see also section.


        """
        out = "See Also\n"
        out += "--------\n"
        if self.config.space_in_see_also_title:
            out += "\n"

        for a, b in sas:
            if b:
                desc = b[0]
            else:
                desc = None
            if len(b) > 1:
                rest_desc = b[1:]
            else:
                rest_desc = []
            _first = True
            for ref, type_ in a:
                # if len(a) > 1:
                #    assert type_ is None, a # matplotlib mlab cohere
                if not _first:
                    out += ", "
                if type_ is not None:
                    out += f":{type_}:`{ref}`"
                else:
                    out += f"{ref}"
                _first = False

            if desc:
                if len(a) > 1 or (not compact):
                    out += f" :\n    {desc}"
                else:
                    attempt = f" : {desc}"
                    if len(out.splitlines()[-1] + attempt) > 80 and not force_compact:
                        return None
                    out += attempt
            for rd in rest_desc:
                out += "\n    " + rd
            out += "\n"
        return out

    @classmethod
    def format_References(cls, lines, compact):
        out = "References\n"
        out += "----------\n"
        out += "\n".join(lines)
        out += "\n"
        return out

    def format_Notes(self, lines, compact):
        out = "Notes\n"
        out += "-----\n"
        if self.config.space_in_notes_title:
            out += "\n"
        out += "\n".join(lines)
        out += "\n"
        return out

    @classmethod
    def format_Examples(cls, lines, compact):
        out = "Examples\n"
        out += "--------\n"
        out += "\n".join(lines)
        out += "\n"
        return out

    @classmethod
    def format_Warnings(cls, lines, compact):
        out = "Warnings\n"
        out += "--------\n"
        out += "\n".join(lines)
        out += "\n"
        return out

    @classmethod
    def format_Warns(cls, ps, compact):
        return cls.format_RRY("Warns", ps)

    @classmethod
    def format_Raises(cls, ps, compact):
        return cls.format_RRY("Raises", ps)

    @classmethod
    def format_Yields(cls, ps, compact):
        return cls.format_RRY("Yields", ps)

    @classmethod
    def format_Returns(cls, ps, compact):
        return cls.format_RRY("Returns", ps)

    @classmethod
    def format_Attributes(cls, ps, compact):
        return cls.format_RRY("Attributes", ps)

    @classmethod
    def format_RRY(cls, name, ps):
        out = name + "\n"
        out += "-" * len(name) + "\n"

        if name == "Returns":
            if len(ps) > 1:
                # do heuristic to check we actually have a description list and not a paragraph
                pass

        for i, p in enumerate(ps):
            # if i:
            #    out += "\n"
            if p.type and re.match("\w+:`", p.type):
                print(
                    "Warning numpydoc may have misparsed this section.", p.name, p.type
                )
            if p.name and p.type:
                out += f"""{p.name.strip()} : {p.type.strip()}\n"""
            elif p.name:
                out += f"""{p.name.strip()}\n"""
            else:
                out += f"""{p.type.strip()}\n"""
            if p.desc:
                out += indent("\n".join(p.desc), "    ")
                out += "\n"
        return out


def dedend_docstring(docstring):
    import textwrap

    lines = docstring.splitlines()
    if len(lines) >= 2:
        l0, *lns = docstring.split("\n")
        l0 = textwrap.dedent(l0)
        lns = textwrap.dedent("\n".join(lns)).split("\n")
        docstring = [l0] + lns
    else:
        docstring = textwrap.dedent(docstring).split("\n")
    return "\n".join(docstring)


def parameter_fixer(params, meta_arg, meta, fname, func_name, config, doc):
    assert "Parameters" in doc
    incorrect_number = False
    jump_to_location = False
    if not config.run_fixers:
        return params, jump_to_location
    pnames = [o.strip() for p in params for o in p.name.split(",") if p.name]
    if meta_arg and meta_arg[0] in ["self", "cls"]:
        meta_arg = meta_arg[1:]
    doc_missing = set(meta_arg) - set(pnames) - {"cls"}
    doc_extra = {x for x in set(pnames) - set(meta_arg) if not x.startswith("*")} - {
        "cls",
    }
    for p in params:
        if p[1].startswith("<"):
            jump_to_location = True
    assert doc_extra != {""}, (set(meta), set(meta_arg), params)
    # don't considert template parameter from numpy/scipy
    doc_extra = {x for x in doc_extra if not (("$" in x) or ("%" in x))}

    def rename_param(source, target):
        renamed = False
        for i, p in enumerate(params):
            if p.name == source:
                params[i] = nds.Parameter(target, *p[1:])
                renamed = True
                break
        return renamed

    if doc_missing and doc_extra:
        # we need to match them maybe:
        # are we missing *, ** in args, and kwargs ?

        for stars in ("*", "**"):
            n_star_missing = doc_missing.intersection({stars + k for k in doc_extra})
            if n_star_missing:
                correct = list(n_star_missing)[0]
                incorrect = correct[len(stars) :]
                rename_param(incorrect, correct)
                doc_missing.remove(correct)
                doc_extra.remove(incorrect)
        for param in list(doc_extra):
            if (
                param.startswith(('"', "'"))
                and param.endswith(('"', "'"))
                and param[1:-1] in doc_missing
            ):
                correct = param[1:-1]
                rename_param(param, correct)
                print("unquote", param, "to", correct)
                doc_missing.remove(correct)
                doc_extra.remove(param)

        if len(doc_missing) == len(doc_extra) == 1:
            correct = list(doc_missing)[0]
            incorrect = list(doc_extra)[0]
            do_rename = True
            if "*" in correct and ("*" not in incorrect):
                if correct.replace("*", "") != incorrect.replace("*", ""):
                    # this is likely undocumented **kwargs.
                    do_rename = False

            if do_rename:
                if rename_param(incorrect, correct):
                    print(f"{fname}:{func_name}")
                    print(f"    renamed {incorrect!r} to {correct!r}")
                    doc_missing = {}
                    doc_extra = {}
                else:
                    print("  could not fix:", doc_missing, doc_extra)
    if doc_missing and not doc_extra and config.with_placeholder:
        for param in doc_missing:
            if "*" in param:
                continue
            annotation_str = "<Insert Type here>"
            current_param = [m for m in meta["simple"] if m.arg == param]
            assert len(current_param) == 1, (current_param, meta, param)
            current_param = current_param[0]
            if type(current_param.annotation).__name__ == "Name":
                annotation_str = str(current_param.annotation.id)
            doc["Parameters"].append(
                nds.Parameter(
                    param,
                    f"{annotation_str}",
                    ["<Multiline Description Here>"],
                )
            )
    elif (
        (not doc_missing)
        and doc_extra
        and ("Parameters" in doc)  # always True
        and (not meta["varkwargs"])
    ):
        print(f"{fname}:{func_name}")
        to_remove = [p for p in doc["Parameters"] if p[0] in doc_extra]
        for remove_me in to_remove:
            if " " in remove_me.name and not remove_me.type and not remove_me.desc:
                # this is likely some extra text
                continue
            print(
                f"    removing parameters {remove_me!r}",
            )
            params.remove(remove_me)
    elif doc_missing or doc_extra:
        incorrect_number = True
        print(f"{fname}:{func_name}")
        if doc_missing:
            print("  missing:", doc_missing)
        if doc_extra:
            print("  extra:", doc_extra)

    return params, jump_to_location, incorrect_number


def compute_new_doc(docstr, fname, *, level, compact, meta, func_name, config):
    """
    compute a new docstring that shoudl be numpydoc compliant.

    Parameters
    ----------
    docstr : str
        docstring to reformat
    fname : str
        filename of the file beign reformatted (for error messages)
    level : int
        indentation level
    compact : bool
        use compact formating in definition list.
    meta : list
        meta info about the function to verify docstrings, for example
        list of parameters.
    func_name : str
        function name for debug.
    config : <Insert Type here>
        <Multiline Description Here>

    Returns
    -------
    str
        new docstring
    Numpydoc
        parsed numpydoc object
    bool
    bool

    """
    assert config is not None

    fail_check = False
    INDENT = level * " "
    NINDENT = "\n" + INDENT
    original_docstr = docstr
    if len(docstr.splitlines()) <= 1:
        return "", NumpyDocString(""), None, fail_check
    shortdoc = bool(docstr.splitlines()[0].strip())
    short_with_space = False
    if not docstr.startswith(NINDENT):
        if original_docstr[0] == " ":
            short_with_space = True

    long_end = True
    long_with_space = True
    if original_docstr.splitlines()[-1].strip():
        long_end = False
    if original_docstr.splitlines()[-2].strip():
        long_with_space = False

    try:
        doc = NumpyDocString(dedend_docstring(docstr))
    except Exception as e:
        raise type(e)(f"error in {fname}:{func_name}") from e
    if config.run_fixers:
        doc.normalize()
    meta_arg = [m.arg for m in meta["simple"]]
    if meta["varargs"]:
        meta_arg.append("*" + meta["varargs"].arg)
    if meta["varkwargs"]:
        meta_arg.append("**" + meta["varkwargs"].arg)

    jump_to_location = False
    if (params := doc["Parameters"]) and meta:

        params, jump_to_location, incorrect_number = parameter_fixer(
            params, meta_arg, meta, fname, func_name, config, doc
        )
        if incorrect_number:
            fail_check = True

    fmt = ""
    start = True
    # ordered_section is a local patch to that records the docstring order.
    df = SectionFormatter(conf=config)
    for s in getattr(doc, "ordered_sections", doc.sections):
        if doc[s]:
            f = getattr(df, "format_" + s.replace(" ", "_"))
            res = f(doc[s], compact)
            if not res:
                continue
            if not start:
                fmt += "\n"
            start = False
            fmt += res
    fmt = indent(fmt, INDENT) + INDENT

    # hack to detect if we have seen a header section.
    if "----" in fmt or True:
        if long_with_space:
            fmt = fmt.rstrip(" ") + NINDENT
        else:
            fmt = fmt.rstrip(" ") + INDENT
    if shortdoc:
        fmt = fmt.lstrip()
        if short_with_space:
            fmt = " " + fmt
    else:
        fmt = "\n" + fmt
    if not long_end:
        fmt = fmt.rstrip()
    assert fmt
    # we can't just do that as See Also and a few other would be sphinxified.
    # return indent(str(doc),'    ')+'\n    '
    if fmt != original_docstr:
        fail_check = True
    return fmt, doc, jump_to_location, fail_check


def reformat_file(data, filename, compact, unsafe, fail=False, config=None, obj_p=None):
    """
    Parameters
    ----------
    compact : bool
        wether to use compact formatting
    data : <Insert Type here>
        <Multiline Description Here>
    unsafe : bool
        <Multiline Description Here>
    fail : <Insert Type here>
        <Multiline Description Here>
    config : <Insert Type here>
        <Multiline Description Here>
    filename : <Insert Type here>
        <Multiline Description Here>

    """
    return _reformat_file(
        data, filename, compact, unsafe, fail=False, config=None, obj_p=None
    )[0]


def _reformat_file(
    data, filename, compact, unsafe, fail=False, config=None, obj_p=None
):
    """
    Parameters
    ----------
    compact : bool
        wether to use compact formatting
    data : <Insert Type here>
        <Multiline Description Here>
    unsafe : bool
        <Multiline Description Here>
    fail : <Insert Type here>
        <Multiline Description Here>
    config : <Insert Type here>
        <Multiline Description Here>
    filename : <Insert Type here>
        <Multiline Description Here>

    Returns
    -------
    str
        The new file
    bool
        Whether this file should fail under the --check flag

    """
    fail_check = False
    assert config is not None

    tree = ast.parse(data, filename)
    new = data

    # funcs = [t for t in tree.body if isinstance(t, ast.FunctionDef)]
    funcs = NodeVisitor({"skip": obj_p})
    funcs.visit(tree)
    funcs = funcs.items
    for i, (func, meta, qname) in enumerate(funcs[:]):
        # print(i, "==", func.name, "==")
        try:
            e0 = func.body[0]
            if not isinstance(e0, ast.Expr):
                continue
            # e0.value is _likely_ a Constant node.
            docstring = e0.value.s
            func_name = func.name
        except AttributeError:
            continue
        if not isinstance(docstring, str):
            continue
        start, nindent, _ = (
            func.body[0].lineno,
            func.body[0].col_offset,
            func.body[0].end_lineno,
        )
        # if not docstring in data:
        #    print(f"skip {file}: {func.name}, can't do replacement yet")
        try:
            new_doc, d_, jump_to_loc, _fail_check = compute_new_doc(
                docstring,
                filename,
                level=nindent,
                compact=compact,
                meta=meta,
                func_name=func_name,
                config=config,
            )
            if _fail_check:
                fail_check = True
            if jump_to_loc:
                print("mvim", f"+{start}", filename)
                pass
                # call editor with file and line number
            elif not unsafe:
                _, d2, _, _fail_check = compute_new_doc(
                    docstring,
                    filename,
                    level=nindent,
                    compact=compact,
                    meta=meta,
                    func_name=func_name,
                    config=config,
                )
                if _fail_check:
                    fail_check = True
                if not d2._parsed_data == d_._parsed_data:
                    secs1 = {
                        k: v
                        for k, v in d2._parsed_data.items()
                        if v != d_._parsed_data[k]
                    }
                    secs2 = {
                        k: v
                        for k, v in d_._parsed_data.items()
                        if v != d2._parsed_data[k]
                    }
                    raise ValueError(
                        "Numpydoc parsing seem to differ after reformatting, this may be a reformatting bug. Rerun with `velin --unsafe "
                        + str(filename)
                        + ":"
                        + qname
                        + "`\n"
                        + str(secs1)
                        + "\n"
                        + str(secs2),
                    )
        except Exception as e:
            print(f"something went wrong with {filename}:{qname} :\n\n{docstring}")
            if fail:
                raise
            else:
                print(e)
            continue
        if not docstring.strip():
            print("DOCSTRING IS EMPTY !!!", func.name)
        # test(docstring, file)
        if new_doc.strip() and new_doc != docstring:
            # need_changes.append(str(filename) + f":{start}:{func.name}")
            if ('"""' in new_doc) or ("'''" in new_doc):
                # print(
                #    "SKIPPING", filename, func.name, "triple quote not handled", new_doc
                # )
                pass
            else:
                # if docstring not in new:
                #    print("ESCAPE issue:", docstring)
                new = new.replace(docstring, new_doc)
            fail_check = True
    return new, fail_check


class SkipPattern:
    def __init__(self, value):
        if ":" in value:
            self.file_pattern, self.obj_pattern = value.split(":")
        else:
            self.file_pattern, self.obj_pattern = value, None

    @property
    def file(self):
        if "*" in self.file_pattern:
            return self.file_pattern + ""
        else:
            return ".*" + self.file_pattern + ".*"

    def __repr__(self):
        return f"<SkipPattern {self.file}>"


def main():
    _config = ConfigParser()
    patterns = []
    if Path("setup.cfg").exists():
        _config.read("setup.cfg")
        patterns = [
            SkipPattern(x.strip())
            for x in _config.get("velin", "ignore_patterns", fallback="").split("\n")
            if x
        ]

    parser = argparse.ArgumentParser(description="reformat the docstrigns of some file")
    parser.add_argument(
        "paths",
        metavar="path",
        type=str,
        nargs="+",
        help="Files or folder to reformat",
    )
    parser.add_argument(
        "--context",
        metavar="context",
        type=int,
        default=3,
        help="Number of context lines in the diff",
    )
    parser.add_argument(
        "--unsafe",
        action="store_true",
        help="Lift some safety feature (don't fail if updating the docstring is not indempotent",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the list of files/lines number and exit with a non-0 exit status, Use it for CI.",
    )
    parser.add_argument(
        "--no-diff",
        action="store_false",
        dest="print_diff",
        help="Do not print the diff",
    )
    parser.add_argument(
        "--black",
        action="store_true",
        dest="run_black",
        help="Do not run black on examples",
    )
    parser.add_argument(
        "--with-placeholder",
        action="store_true",
        dest="with_placeholder",
        help="insert missing sections/parameters placehoders",
    )
    parser.add_argument("--no-color", action="store_false", dest="do_highlight")
    parser.add_argument("--compact", action="store_true", help="Please ignore")
    parser.add_argument("--no-fail", action="store_false", dest="fail")
    parser.add_argument(
        "--space-in-see-also-title", action="store_true", dest="space_in_see_also_title"
    )
    parser.add_argument(
        "--space-in-notes-title", action="store_true", dest="space_in_notes_title"
    )
    parser.add_argument(
        "--no-fixers",
        action="store_false",
        dest="run_fixers",
        help="try to only reformat and does not run fixers heuristics",
    )
    parser.add_argument(
        "--write",
        dest="write",
        action="store_true",
        help="Try to write the updated docstring to the files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="increase the verbosity of the output",
    )

    args = parser.parse_args()

    config = Config(
        {
            "with_placeholder": args.with_placeholder,
            "compact_param": args.compact,
            "space_in_see_also_title": args.space_in_see_also_title,
            "space_in_notes_title": args.space_in_notes_title,
            "run_fixers": args.run_fixers,
        }
    )
    global BLACK_REFORMAT
    if args.run_black:
        BLACK_REFORMAT = True
    else:
        BLACK_REFORMAT = False

    global print
    if args.verbose:
        try:
            from there import print
        except ImportError:
            pass

    to_format = []

    for f in args.paths:
        p = Path(f)
        if p.is_dir():
            for sf in p.glob("**/*.py"):
                to_format.append(sf)
        else:
            to_format.append(p)

    def to_skip(file, patterns):
        for p in patterns:
            if re.match(p.file, file):
                if p.obj_pattern is None:
                    return True
                else:
                    continue
        return False

    need_changes = []
    for file in to_format:
        if to_skip(str(file), patterns):
            print("ignoring", file)
            continue

        try:
            with open(file) as f:
                data = f.read()
        except Exception as e:
            # continue
            continue
            raise RuntimeError(f"Fail reading {file}") from e

        obj_p = [p.obj_pattern for p in patterns if re.match(p.file, str(file))]
        new, _fail_check = _reformat_file(
            data,
            file,
            args.compact,
            args.unsafe,
            fail=args.fail,
            config=config,
            obj_p=obj_p,
        )
        # test(docstring, file)
        if new != data:
            need_changes.append(str(file))

            dold = data.splitlines()
            dnew = new.splitlines()
            diffs = list(
                difflib.unified_diff(
                    dold, dnew, n=args.context, fromfile=str(file), tofile=str(file)
                ),
            )

            if args.print_diff and not args.write:
                code = "\n".join(diffs)

                if args.do_highlight:
                    from pygments import highlight
                    from pygments.formatters import TerminalFormatter
                    from pygments.lexers import DiffLexer

                    code = highlight(code, DiffLexer(), TerminalFormatter())

                print(code)
            if args.write:
                with open(file, "w") as f:
                    f.write(new)
        elif _fail_check:
            need_changes.append(str(file))

    if args.check:
        if len(need_changes) != 0:
            sys.exit(
                "Some files/functions need updates:\n - " + "\n - ".join(need_changes)
            )
        else:
            sys.exit(0)
