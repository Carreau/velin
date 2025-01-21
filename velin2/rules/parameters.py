from velin2.rules.core import lang_rst, register_rule


def custom_predicates(predicate, args, pattern_index, captures):
    match predicate:
        case "not-definition-list?":
            if len(args) != 1 or (type_ := args[0][1]) != "capture":
                type_name = type_ if type_ != "capture" else "capture name"
                raise TypeError(
                    f"predicate {predicate} requires exactly one capture name."
                    f" Got {args[0][0]} (a {type_name}) instead."
                )

            # query guarantees that the capture name exists
            nodes = captures[args[0][0]]

            return all(node.type != "definition_list" for node in nodes)

    raise TypeError(f"unknown predicate: {predicate}")


@register_rule(
    "V100",
    "Parameters must be formatted as a definition list",
)
def check_format_as_definition_list(tree, context):
    # '((section (title) @title (#eq? @title "Parameters")) (_)+ @content)'
    query = lang_rst.query(
        """
        (
          (section (title) @title (#eq? @title "Parameters"))
          .
          ((_) @node (#not-definition-list? @node)) @content
        )
        """
    )

    result = query.captures(tree.root_node, predicate=custom_predicates)

    violations = [node for node in result.get("content", [])]
    suggestions = [_ for _ in violations]
    return zip(violations, suggestions)
