import itertools


def format_report(violations):
    # collapse the list of list of violations
    collapsed = list(itertools.chain.from_iterable(violations))
    if not collapsed:
        return ""

    sorted_ = sorted(collapsed, key=lambda x: x.point[0])
    return "\n".join(str(violation) for violation in sorted_)
