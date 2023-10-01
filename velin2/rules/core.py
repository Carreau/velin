from dataclasses import dataclass

rules = {}


@dataclass
class Rule:
    checker: callable
    description: str


def register_rule(code, description):
    def outer(f):
        if code in rules:
            raise ValueError(f"code {code} exists already. Refusing to overwrite")

        rules[code] = Rule(checker=f, description=description)

        return f

    return outer
