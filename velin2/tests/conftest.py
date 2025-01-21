import pytest

from velin2.rules import core


@pytest.fixture
def rules(monkeypatch):
    class IsolatedRules:
        def isolate(self, rules: str | list[str]):
            if isinstance(rules, str):
                rules = [rules]
            isolated_rules = {
                name: rule for name, rule in core.rules.items() if name in rules
            }
            monkeypatch.setattr(core, "rules", isolated_rules)

    yield IsolatedRules()
