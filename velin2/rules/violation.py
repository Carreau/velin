import attrs


@attrs.define
class Violation:
    path = attrs.field()

    docstring_node = attrs.field()
    column_offsets = attrs.field()
    offending_node = attrs.field()

    error_code = attrs.field()
    description = attrs.field()

    suggestions = attrs.field()
