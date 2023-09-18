import itertools


def format_lint(path, root, code, node):
    # the lint reports:
    # 1. the code position as path / line number / column index
    # 2. the error code
    # 3. human readable description of what went wrong
    # 4. code print

    root_line, root_column = root.start_point
    node_line, node_column = node.start_point

    # To figure out the line number, we need to:
    # 1. add root and node line numbers
    # 2. adjust for anything inspect.cleandoc did
    #    For lines, it should only remove empty lines at the top
    # 3. add 1 to make the lines 1-based
    lines = list(line.lstrip() for line in root.text.decode().split("\n"))
    n_prefix_lines = len(list(itertools.takewhile(lambda line: not line, lines)))
    line = root_line + node_line + n_prefix_lines + 1

    # Figuring out the column index is very similar, except adjusting for inspect.cleandoc
    # is much more tricky
    column = 0

    # TODO: figure out whether to format the description here or to propagate a single
    # "report" object per rule violation
    description = ""
    return f"{path}:{line}:{column}: {code}: {description} ({node.text.decode()})"


def format_report(path, docstring, violations):
    collapsed = list(
        itertools.chain.from_iterable(
            ((code, node) for node in violating_nodes)
            for code, violating_nodes in violations.items()
            if violating_nodes
        )
    )
    sorted_ = sorted(collapsed, key=lambda x: x[1].start_point)

    formatted = [format_lint(path, docstring, code, node) for code, node in sorted_]
    return "\n".join(formatted)
