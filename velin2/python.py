from velin2.parser import get_language


def extract_string(node):
    return node.child(1)


def extract_docstring_nodes(tree):
    query_statement = """
      [
        (module . (comment)+ (expression_statement (string) @docstring))
        (function_definition (block . (expression_statement (string) @docstring)))
        (class_definition (block . (expression_statement (string) @docstring)))
      ] @parent
    """
    lang_py = get_language("python")

    query = lang_py.query(query_statement)
    captures = query.captures(tree.root_node)
    parents = captures.get("parent", [])

    docstrings = [extract_string(node) for node in captures.get("docstring", [])]

    return zip(docstrings, parents)


def extract_identifier(node):
    if node.type in {"identifier", "list_splat_pattern", "dictionary_splat_pattern"}:
        return node

    return node.child_by_field_name("name")


def extract_parameter_names(node):
    parameter_field = node.child_by_field_name("parameters")

    identifier_types = {
        "identifier",
        "list_splat_pattern",
        "dictionary_splat_pattern",
        "default_parameter",
        "typed_default_parameter",
    }

    identifiers = [
        extract_identifier(node)
        for node in parameter_field.children
        if node.type in identifier_types
    ]

    return identifiers
