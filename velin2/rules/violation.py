from functools import cached_property

import attrs


@attrs.define(slots=False)
class Violation:
    path = attrs.field()

    docstring_node = attrs.field()
    column_offsets = attrs.field()
    offending_node = attrs.field()

    error_code = attrs.field()
    description = attrs.field()

    suggestions = attrs.field()

    @cached_property
    def point(self):
        local_line_index = self.offending_node.start_point[0]

        line_index = self.docstring_node.start_point[0] + local_line_index
        line_number = line_index + 1

        column_number = (
            self.offending_node.start_point[1] + self.column_offsets[local_line_index]
        )

        return line_number, column_number

    def __str__(self):
        line, column = self.point

        return "\n".join(
            [
                f"{self.path}:{line}:{column}: {self.error_code}: {self.description}",
                self.offending_node.text.decode(),
            ]
        )
