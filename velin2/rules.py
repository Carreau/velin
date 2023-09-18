import inspect

from .parser import get_language, get_parser

# rules
# 1. section titles
#   2. section names must be part of a small subset
#   3. section names must be in title case
#   4. section underline must be `-` and have the same length as the section name
# 2. section structure
#   1. sections must be preceded by a newline
# 3. section order:
#   1. signature (on its own line, not with the triple quotes)
#   2. short summary (if signature: separated by newline, else: on triple-quote line)
#   3. deprecation warning using the directive
#   4. extended summary (prose)
#   5. parameters
#   6. attributes (if class docstring)
#   7. returns
#   8. yields
#   9. receives
#  10. other parameters
#  11. raises
#  12. warns
#  13. warnings (cautions in prose)
#  14. see also
#  15. notes
#  16. references
#  17. examples
lang_rst = get_language("rst")
parser_rst = get_parser("rst")

valid_section_names = [
    "Parameters",
    "Attributes",
    "Returns",
    "Yields",
    "Receives",
    "Other parameters",
    "Raises",
    "Warns",
    "Warnings",
    "See also",
    "Notes",
    "References",
    "Examples",
]


def check_section_title_case(tree):
    query = lang_rst.query("(section (title) @title)")
    titles = [node for node, _ in query.captures(tree.root_node)]

    violations = [node for node in titles if not node.text.decode().istitle()]
    return violations


def check_section_name(tree):
    query = lang_rst.query("(section (title) @title)")
    titles = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node for node in titles if node.text.decode().title() not in valid_section_names
    ]
    return violations


def check_section_adornment_position(tree):
    """section titles must have only an underline"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node
        for node in sections
        if [c.type for c in node.children] != ["title", "adornment"]
    ]
    return violations


def check_section_adornment_char(tree):
    """section adornment must consist only of '-'"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node
        for node in sections
        if all(
            set(c.text.decode()) == {"-"}
            for c in node.children
            if c.type == "adornment"
        )
    ]
    return violations


def check_section_adornment_length(tree):
    """section adornment must only have the same length as the title"""
    query = lang_rst.query("(section) @section")
    sections = [node for node, _ in query.captures(tree.root_node)]

    violations = [
        node for node in sections if len(node.child(1).text) != len(node.child(0).text)
    ]
    return violations


rules = {
    "V001": check_section_title_case,
    "V002": check_section_name,
    "V003": check_section_adornment_position,
    "V004": check_section_adornment_length,
    "V005": check_section_adornment_char,
}


def check_docstring_rules(node):
    cleaned_docstring = inspect.cleandoc(node.text.decode()).encode()

    parsed = parser_rst.parse(cleaned_docstring)

    violations = {code: checker(parsed) for code, checker in rules.items()}
    # TODO: collapse and sort by violating node's starting point

    return violations
