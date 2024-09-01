# TODO: use tree_sitter_languages instead
import os
import pathlib

from tree_sitter import Language, Parser

languages_path = pathlib.Path.home() / "repos/tree-sitter" / "languages.so"


def get_language(name):
    return Language(os.fspath(languages_path), name)


def get_parser(name):
    language = get_language(name)

    parser = Parser()
    parser.set_language(language)

    return parser
