import attrs


@attrs.define(frozen=True)
class ModifiedLine:
    content = attrs.field()
    removed_chars = attrs.field(default=0)

    def remove_first(self, n_chars):
        if not self.content:
            return self

        return type(self)(self.content[n_chars:], self.removed_chars + n_chars)

    def count_first(self, char):
        return len(self.content) - len(self.content.lstrip(char))


def remove_leading_whitespace(line):
    n_chars = line.count_first(" ")

    return line.remove_first(n_chars)


def remove_common_indentation(lines):
    indents = {line.count_first(" ") for line in lines}

    try:
        common_indentation = min(indents - {0})
    except ValueError:
        common_indentation = 0

    if common_indentation == 0:
        return lines

    return [line.remove_first(common_indentation) for line in lines]


def cleandoc(docstring):
    """like `inspect.cleandoc`, but keep track of what we're removing"""
    if "\t" in docstring:
        raise ValueError("cannot work with tabs")

    lines = [ModifiedLine(line) for line in docstring.splitlines()]

    # steps (skip 3 and 4):
    # 1. remove leading whitespace from the first line
    lines[0] = remove_leading_whitespace(lines[0])
    # 2. remove common whitespace from the second line onwards
    lines[1:] = remove_common_indentation(lines[1:])
    # 3. remove leading and trailing empty lines
    # 4. replace tabs with spaces

    result = "\n".join(line.content for line in lines)
    removed_chars = [line.removed_chars for line in lines]

    return result, removed_chars
