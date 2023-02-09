# Vélin

French for Vellum

> Vellum is prepared animal skin or "membrane", typically used as a material for writing on. Parchment is another term
> for this material, and if vellum is distinguished from this, it is by vellum being made from calfskin, as opposed to
> that from other animals,[1] or otherwise being of higher quality


## install

You may need to get a modified version of numpydoc depending on the stage of development.

```
$ git clone https://github.com/Carreau/velin
$ cd velin
$ pip install -e . 
```

(You will need a quite recent pip and flit to do so)

## Autoreformat docstrings

This assume your docstrings are in RST/Numpydoc format, and will try to fix
common formatting mistakes and typo.


```
velin [--write] <path-to-file.py> or <path-to-dir>
```

Without `--write` vélin will print the suggested diff, with `--write` it will _attempt_  to update the files.

## options

(likely not up to date, make sure to run `velin --help` to check for new,changed
or removed options)

```
$ velin --help
usage: velin [-h] [--context context] [--unsafe] [--check] [--no-diff] [--black] [--with-placeholder] [--no-color] [--compact] [--no-fail]
             [--space-in-see-also-title] [--space-in-notes-title] [--no-fixers] [--write]
             path [path ...]

reformat the docstrings of some file

positional arguments:
  path                  Files or folder to reformat

optional arguments:
  -h, --help            show this help message and exit
  --context context     Number of context lines in the diff
  --unsafe              Lift some safety feature (don't fail if updating the docstring is not indempotent)
  --check               Print the list of files/lines number and exit with a non-0 exit status. Specify this to use it for CI.
  --no-diff             Do not print the diff
  --black               Do not run black on examples
  --with-placeholder    insert missing sections/parameters placeholders
  --no-color
  --compact             Please ignore
  --no-fail
  --space-in-see-also-title
  --space-in-notes-title
  --no-fixers           try to only reformat and does not run fixers heuristics
  --write               Try to write the updated docstring to the files
```

## --no-fixers

Beyond reformatting, vélin will by default try to run a number of heuristics to update your docstrings:

  - Remove non existing but documented parameters,
  - Rename parameter with typos,
  - insert space before colon when necessary.

Unfortunately sometime those heuristics can remove actual content, for example in the malformed DocString below, the
Return section would be removed


```
def sum(a, b):
    """
    Parameters
    ----------
    a : int
        a number
    b : int
        another number
    Returns
    -------
    s :
        sum of a and b

    See Also
    --------
    substract
    """
    return a + b

```

As there is a missing blank line before return Numpydoc will parse this a 5
parameters, `a`, `b`, `Returns`, `-------` and `s`. As only `a` and `b` are in
the signature, it will remove the other.

While in this case it will try not to do that because we detect that `------` is
likely an underline, there are other case where it's unclear what to do.

You can thus disable those fixers by passing the option `--no-fixers`




## setup.cfg


Ignore files with ignore_patterns, `filename` or `filename:qualified_name`.
You can (try to), put patterns in there, but it's not guarantied to work yet.

```
[velin]
ignore_patterns =
   path/to/a.py:Class.func
   path/to/b.py:Class.func
```

## kind of things it fixes

 - Spacing around colon,
 - If one parameter has typo wrt function signature: fix it.
 - Insert all missing parameters with placeholders.
