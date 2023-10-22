from velin2.rules.core import lang_rst, register_rule

valid_section_names = [
    "Parameters",
    "Attributes",
    "Returns",
    "Yields",
    "Receives",
    "Other Parameters",
    "Raises",
    "Warns",
    "Warnings",
    "See Also",
    "Notes",
    "References",
    "Examples",
]


@register_rule(
    "V001",
    "\n".join(
        [
            "Section titles must be exactly one of:",
            ", ".join(repr(n) for n in valid_section_names),
        ]
    ),
)
def check_section_name(tree, context):
    query = lang_rst.query("(section (title) @title)")
    titles = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        title for title in titles if title.text.decode() not in valid_section_names
    ]
    suggestions = [[] for node in violations]
    return zip(violations, suggestions)


@register_rule(
    "V002",
    "Section titles can only have a single adornment (an underline).",
)
def check_section_adornment_position(tree, context):
    """section titles must have only an underline"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node
        for node in sections
        if [c.type for c in node.children] != ["title", "adornment"]
    ]
    suggestions = [[] for node in violations]
    return zip(violations, suggestions)


@register_rule(
    "V003",
    "Section title adornments (the underline) must have the same length as the title",
)
def check_section_adornment_length(tree, context):
    """section adornment must have the same length as the title"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node for node in sections if len(node.child(1).text) != len(node.child(0).text)
    ]
    suggestions = [[] for node in violations]
    return zip(violations, suggestions)


@register_rule(
    "V004",
    "Section title adornments (the underline) must solely consist of `-` characters.",
)
def check_section_adornment(tree, context):
    """section adornment must consist only of '-'"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node
        for node in sections
        if any(
            set(c.text.decode()) != {"-"}
            for c in node.children
            if c.type == "adornment"
        )
    ]
    suggestions = [[] for node in violations]
    return zip(violations, suggestions)
