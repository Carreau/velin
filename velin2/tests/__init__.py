class DummyNode:
    def __init__(self):
        self.start_point = (0, 0)


def format_violations(violations):
    return "\n".join(
        [
            "Found the following violations:",
            *(str(violation) for violation in violations),
        ]
    )
