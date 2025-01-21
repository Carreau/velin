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
            """,
            0,
            id="parameters-passing",
        ),
        pytest.param(
            """
            Parameters
            ----------
            a: text
            b: text
            """,
            1,
            id="parameters-failing-paragraph",
        ),
        pytest.param(
            """
            Parameters
            ----------
            - a
            - b
            """,
            1,
            id="parameters-failing-bullet_list",
        ),
        pytest.param(
            """short summary

            Other Parameters
            ----------
            a : int
                description
            """,
            0,
            id="other parameters-passing",
        ),
        pytest.param(
            """
            Other Parameters
            ----------
            a: text
            b: text
            """,
            1,
            id="other parameters-failing-paragraph",
        ),
        pytest.param(
            """
            Other Parameters
            ----------
            - a
            - b
            """,
            1,
            id="other parameters-failing-bullet_list",
        ),
    ),
)
def test_format_as_definition_list(docstring, n_violations, rules):
    rules.isolate("V100")

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
            """
            Parameters
            ----------
            a : int
                description
            """,
            0,
            id="parameters-passing",
        ),
        pytest.param(
            """
            Parameters
            ----------
            1a : int
                description
            """,
            1,
            id="parameters-failing",
        ),
        pytest.param(
            """
            Other Parameters
            ----------------
            a : int
                description
            """,
            0,
            id="other parameters-passing",
        ),
        pytest.param(
            """
            Other Parameters
            ----------------
            1a : int
                description
            """,
            1,
            id="other parameters-failing",
        ),
    ),
)
def test_term_is_a_python_identifier(docstring, n_violations, rules):
    rules.isolate("V110")

    dummy_node = DummyNode()

    cleaned_docstring, column_offsets = cleandoc(docstring)

    tree = parser_rst.parse(cleaned_docstring.encode())
    context = Context("<test example>", dummy_node, column_offsets)

    violations = _check_docstring(tree, context)

    assert len(violations) == n_violations, format_violations(violations)
