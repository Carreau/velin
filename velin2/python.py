import itertools
from .tree import traverse_tree


docstring_node_types = ["module", "function_definition", "class_definition"]


def extract_docstring(node):
    # the docstring starts on the first line of code in the node,
    # minus any comments or empty lines
    for child in node.children:
        if child.type == "comment":
            continue

        if child.type != "expression_statement":
            return None

        if child.child_count != 1:
            return None

        potential_docstring = child.child(0)
        if potential_docstring.type != "string":
            return None

        return potential_docstring


def extract_string_content(node):
    return node.child(1)


def extract_docstring_nodes(tree):
    nodes = traverse_tree(tree)

    for node in nodes:
        if node.type not in docstring_node_types:
            continue

        if node.type == "module":
            docstring = extract_docstring(node)
        else:
            # the docstring is in the block node
            block_node = node.children[-1]
            docstring = extract_docstring(block_node)

        if docstring is None:
            continue

        yield extract_string_content(docstring)
