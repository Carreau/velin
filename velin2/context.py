import attrs


@attrs.define(frozen=True)
class Context:
    path = attrs.field()

    docstring_node = attrs.field()
    column_offsets = attrs.field()
