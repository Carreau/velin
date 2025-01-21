from tree_sitter import Language, Parser


def get_python():
    import tree_sitter_python

    return Language(tree_sitter_python.language())


def get_rst():
    import tree_sitter_rst

    return Language(tree_sitter_rst.language())


def get_language(name):
    names = {
        "python": get_python,
        "rst": get_rst,
    }
    return names[name]()


def get_parser(name):
    language = get_language(name)

    return Parser(language)
