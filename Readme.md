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
$ pip install flit
$ flit install --symlink
```

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
usage: velin [-h] [--context context] [--unsafe] [--check] [--no-diff] [--black] [--with-placeholder] [--no-color] [--compact] [--no-fail] [--write]
             path [path ...]

reformat the docstrigns of some file

positional arguments:
  path                Files or folder to reformat

optional arguments:
  -h, --help          show this help message and exit
  --context context   Number of context lines in the diff
  --unsafe            Lift some safety feature (don't fail if updating the docstring is not indempotent
  --check             Print the list of files/lines number and exit with a non-0 exit status, Use it for CI.
  --no-diff           Do not print the diff
  --black             Do not run black on examples
  --with-placeholder  insert missing sections/parameters placehoders
  --no-color
  --compact           Please ignore
  --no-fail
  --write             Try to write the updated docstring to the files
```


## setup.cfg


Ignore files with comma separated ignore_patterns

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
