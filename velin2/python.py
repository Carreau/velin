from .parser import get_language


def extract_string(node):
    return node.child(1)


def extract_docstring_nodes(tree):
    query_statement = """
      [
        (module . (comment)+ (expression_statement (string) @docstring))
        (function_definition (block . (expression_statement (string) @docstring)))
        (class_definition (block . (expression_statement (string) @docstring)))
      ]
    """
    lang_py = get_language("python")

    query = lang_py.query(query_statement)
    return [extract_string(node) for node, _ in query.captures(tree.root_node)]
