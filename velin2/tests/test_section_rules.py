import pytest

from velin2.context import Context
from velin2.docstring import cleandoc
from velin2.rules.core import _check_docstring, parser_rst
from velin2.tests import DummyNode, format_violations


@pytest.mark.parametrize(
    ["docstring", "n_violations"],
    (
        pytest.param(
            """short summary

            Parameters
            ----------
            a : int
                description

            Notes
            -----
            note

            Examples
            --------
            >>> 1
            1
            """,
            0,
            id="passing",
        ),
        pytest.param(
            """short summary
            Parameters
            ----------
            a : int
                description

            Notes
            -----
            note

            Examples
            --------
            >>> 1
            1
            """,
            1,
            id="between summary and parameters",
        ),
        pytest.param(
            """short summary

            Parameters
            ----------
            a : int
                description
            Notes
            -----
            note

            Examples
            --------
            >>> 1
            1
            """,
            1,
            id="between parameters and notes",
            marks=[
                pytest.mark.xfail(
                    reason="needs further investigation and a fix in tree-sitter-rst"
                )
            ],
        ),
        pytest.param(
            """short summary

            Parameters
            ----------
            a : int
                description

            Notes
            -----
            note
            Examples
            --------
            >>> 1
            1
            """,
            1,
            id="between notes and examples",
        ),
    ),
)
def test_blank_line_before_section(docstring, n_violations, rules):
    rules.isolate("V001")

    dummy_node = DummyNode()

    cleaned_docstring, column_offsets = cleandoc(docstring)

    tree = parser_rst.parse(cleaned_docstring.encode())
    context = Context("<test example>", dummy_node, column_offsets)

    violations = _check_docstring(tree, context)

    assert len(violations) == n_violations, format_violations(violations)


@pytest.mark.parametrize(
    ["docstring", "n_violations"],
    (
        pytest.param(
            """short summary

            Parameters
            ----------
            a : int
                description

            Returns
            -------
            a : int
                description
            """,
            0,
            id="passing",
        ),
        pytest.param(
            """short summary

            Paramters
            ----------
            a : int
                description

            Returns
            -------
            a : int
                description
            """,
            1,
            id="misspelled parameters",
        ),
        pytest.param(
            """short summary

            Args
            ----
            a : int
                description

            Returns
            -------
            a : int
                description
            """,
            1,
            id="invalid section",
        ),
        pytest.param(
            """short summary

            Parameters
            ----------
            a : int
                description

            results
            -------
            a : int
                description
            """,
            1,
            id="misspelled results",
        ),
    ),
)
def test_section_name(docstring, n_violations, rules):
    rules.isolate("V002")

    dummy_node = DummyNode()

    cleaned_docstring, column_offsets = cleandoc(docstring)

    tree = parser_rst.parse(cleaned_docstring.encode())
    context = Context("<test example>", dummy_node, column_offsets)

    violations = _check_docstring(tree, context)

    assert len(violations) == n_violations, format_violations(violations)
