from dataclasses import dataclass


class AvgSyntaxError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CommandLine:
    name: str
    attributes: dict[str, str]
    body: str
    raw: str


def _split_outside_quotes(value: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote is not None:
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == delimiter:
            parts.append(value[start:index])
            start = index + 1
    if quote is not None:
        raise AvgSyntaxError("属性值的引号未闭合")
    parts.append(value[start:])
    return parts


def _find_outside_quotes(value: str, target: str) -> int:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote is not None:
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == target:
            return index
    return -1


def _decode_value(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or value[0] not in {'"', "'"} or value[-1] != value[0]:
        return value

    quote = value[0]
    decoded: list[str] = []
    index = 1
    while index < len(value) - 1:
        character = value[index]
        if character == "\\" and index + 1 < len(value) - 1:
            following = value[index + 1]
            if following in {quote, "\\"}:
                decoded.append(following)
                index += 2
                continue
        decoded.append(character)
        index += 1
    return "".join(decoded)


def parse_attributes(value: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    positional: list[str] = []
    for part in _split_outside_quotes(value, ","):
        part = part.strip()
        if not part:
            continue
        equals = _find_outside_quotes(part, "=")
        if equals < 0:
            positional.append(_decode_value(part))
            continue
        key = part[:equals].strip()
        if not key:
            raise AvgSyntaxError("属性名为空")
        attributes[key] = _decode_value(part[equals + 1 :])
    if positional:
        attributes["_positional"] = ";".join(positional)
    return attributes


def _find_closing_bracket(line: str, start: int) -> int:
    quote: str | None = None
    escaped = False
    for index in range(start + 1, len(line)):
        character = line[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote is not None:
            if character == quote:
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == "]":
            return index
    raise AvgSyntaxError("指令缺少右方括号")


def parse_command_line(line: str) -> CommandLine | None:
    stripped = line.lstrip()
    if not stripped.startswith("["):
        return None

    start = len(line) - len(stripped)
    end = _find_closing_bracket(line, start)
    header = line[start + 1 : end].strip()
    if not header:
        raise AvgSyntaxError("指令名为空")

    open_parenthesis = _find_outside_quotes(header, "(")
    if open_parenthesis >= 0:
        if not header.endswith(")"):
            raise AvgSyntaxError("指令参数缺少右括号")
        name = header[:open_parenthesis].strip()
        argument_text = header[open_parenthesis + 1 : -1]
    else:
        equals = _find_outside_quotes(header, "=")
        if equals >= 0:
            name = header[:equals].strip()
            argument_text = header
        else:
            name = header
            argument_text = ""

    if not name:
        raise AvgSyntaxError("指令名为空")
    return CommandLine(
        name=name,
        attributes=parse_attributes(argument_text),
        body=line[end + 1 :].strip(),
        raw=line,
    )
