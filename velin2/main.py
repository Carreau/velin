import argparse
import pathlib
import sys

from .parser import get_parser
from .python import extract_docstring_nodes
from .report import format_report
from .rules import check_docstring_rules


def process_file(path):
    parser = get_parser("python")

    tree = parser.parse(path.read_bytes())
    docstring_nodes = extract_docstring_nodes(tree)
    rule_violations = [(node, check_docstring_rules(node)) for node in docstring_nodes]

    reports = [
        format_report(path, node, violations)
        for node, violations in rule_violations
        if any(entry for entry in violations.values())
    ]

    return "\n".join(reports)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=pathlib.Path)

    args = parser.parse_args()

    violations_found = False
    for path in args.paths:
        report = process_file(path)
        if not report:
            continue

        violations_found = True
        print(report)

    sys.exit(0 if not violations_found else 1)
