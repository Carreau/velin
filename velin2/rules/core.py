import attrs

from velin2.context import Context
from velin2.docstring import cleandoc
from velin2.parser import get_language, get_parser
from velin2.rules.violation import Violation

lang_rst = get_language("rst")
parser_rst = get_parser("rst")


rules = {}


@attrs.define
class Rule:
    checker = attrs.field()

    error_code = attrs.field()
    description = attrs.field()

    def check(self, tree, context):
        offending_nodes = self.checker(tree, context)
        violations = [
            Violation(
                path=context.path,
                docstring_node=context.docstring_node,
                column_offsets=context.column_offsets,
                offending_node=node,
                error_code=self.error_code,
                description=self.description,
                suggestions=suggestions,
            )
            for node, suggestions in offending_nodes
        ]

        return violations


def register_rule(code, description):
    """register a validation rule"""

    def outer(f):
        if code in rules:
            raise ValueError(f"code {code} exists already. Refusing to overwrite")

        rules[code] = Rule(checker=f, error_code=code, description=description)

        return f

    return outer


def check_docstring(path, node):
    cleaned_docstring, column_offsets = cleandoc(node.text.decode())
    context = Context(path, node, column_offsets)

    tree = parser_rst.parse(cleaned_docstring.encode())

    violations = {code: rule.check(tree, context) for code, rule in rules.items()}

    return violations
