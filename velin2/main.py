import argparse
import pathlib
import sys

from velin2.parser import get_parser
from velin2.python import extract_docstring_nodes
from velin2.report import format_report
from velin2.rules import check_docstring


def process_file(path):
    parser = get_parser("python")

    tree = parser.parse(path.read_bytes())
    docstring_nodes = extract_docstring_nodes(tree)
    violations = [check_docstring(path, node) for node in docstring_nodes]

    return format_report(violations)


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
