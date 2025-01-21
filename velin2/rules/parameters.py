from velin2.rules.core import lang_rst, register_rule

query_parameters = """
(
  section (title) @title
  (#any-of? @title "Parameters" "Other Parameters")
)
"""


def format_type(type_):
    return type_ if type_ != "capture" else "capture name"


def validate_parameter_types(types_, expected_types, predicate):
    if types_ == expected_types:
        return

    if len(expected_types) == 1:
        type_names = map(format_type, types_)
        expected_type_name = format_type(expected_types[0])

        msg = (
            f"predicate {predicate} requires exactly one {expected_type_name}."
            f" Got [{', '.join(type_names)}] instead."
        )
    else:
        type_names = map(format_type, types_)
        expected_type_names = map(format_type, expected_types)
        msg = (
            "Unexpected argument types."
            f" Expected [{', '.join(expected_type_names)}],"
            f" but got [{', '.join(type_names)}]."
        )

    raise TypeError(msg)


def custom_predicates(predicate, args, pattern_index, captures):
    types_ = [type_ for _, type_ in args]
    values = [value for value, _ in args]
    match predicate:
        case "not-definition-list?":
            validate_parameter_types(types_, ["capture"], predicate)

            # query guarantees that the capture name exists
            nodes = captures[values[0]]

            return any(node.type != "definition_list" for node in nodes)

        case "python-identifier?":
            validate_parameter_types(types_, ["capture"], predicate)

            nodes = captures[values[0]]

            return any(not node.text.decode().isidentifier() for node in nodes)

    raise TypeError(f"unknown predicate: {predicate}")


@register_rule(
    "V100",
    "Parameters must be formatted as a definition list",
)
def check_format_as_definition_list(tree, context):
    query = lang_rst.query(
        f"""
        (
          {query_parameters}
          .
          ((_) @node (#not-definition-list? @node)) @content
        )
        """
    )

    result = query.captures(tree.root_node, predicate=custom_predicates)

    violations = [node for node in result.get("content", [])]
    suggestions = [_ for _ in violations]
    return zip(violations, suggestions)


@register_rule(
    "V110",
    "Listed parameters must be valid python identifiers.",
)
def check_term_is_a_python_identifier(tree, context):
    query = lang_rst.query(
        f"""
        (
          {query_parameters}
          .
          (
            definition_list
            (list_item (term) @term (#python-identifier? @term))
          )
        )
        """
    )

    result = query.captures(tree.root_node, predicate=custom_predicates)

    violations = [node for node in result.get("term", [])]
    suggestions = [_ for _ in violations]

    return zip(violations, suggestions)
