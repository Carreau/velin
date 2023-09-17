def _traverse(node):
    yield node

    yield from itertools.chain.from_iterable(map(_traverse, node.children))


def traverse_tree(tree):
    yield from _traverse(tree.root_node)
