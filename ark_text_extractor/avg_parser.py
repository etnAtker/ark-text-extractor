from collections.abc import Iterable
from pathlib import Path
import re

from .avg_syntax import AvgSyntaxError, CommandLine, parse_command_line
from .command_registry import (
    COMMAND_KINDS,
    DECLARED_NON_TEXT_ATTRIBUTES,
    DECLARED_TEXT_ATTRIBUTES,
    SUSPECT_TEXT_ATTRIBUTE,
    CommandKind,
)
from .domain import (
    ChoiceOption,
    EventKind,
    ParseResult,
    SourceLocation,
    TextEvent,
)
from .known_warnings import is_known_trailing_noise


PARAGRAPH_TAG = re.compile(r"<p\s*=\s*[^>]+>", re.IGNORECASE)
STYLE_TAG = re.compile(
    r"</>|<@[A-Za-z0-9_.]+(?:=[^>]*)?>|</?color(?:=[^>]*)?>|"
    r"</?size(?:=[^>]*)?>|</?[ib]>",
    re.IGNORECASE,
)
VISIBLE_CJK = re.compile(r"[\u3400-\u9fff]")
BODY_COMMAND_KINDS = frozenset(
    {
        CommandKind.DIALOGUE_BODY,
        CommandKind.NARRATION_BODY,
        CommandKind.SCREEN_BODY,
        CommandKind.METADATA_BODY,
    }
)


class UnknownCommandError(ValueError):
    pass


class UnexpectedCommandTextError(ValueError):
    pass


def normalize_text(value: str) -> str:
    value = value.replace(r"\n", "\n")
    value = PARAGRAPH_TAG.sub("\n", value)
    value = STYLE_TAG.sub("", value)
    lines = (line.strip() for line in value.splitlines())
    return "\n".join(line for line in lines if line).strip()


def _attribute(attributes: dict[str, str], key: str) -> str | None:
    normalized_key = key.casefold()
    return next(
        (
            value
            for name, value in attributes.items()
            if name.casefold() == normalized_key
        ),
        None,
    )


def _is_true(value: str | None) -> bool:
    return value is not None and value.casefold() in {"1", "true", "yes"}


def _split_semicolon(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in value.split(";") if part.strip())


def _logical_lines(text: str) -> Iterable[tuple[int, str]]:
    parts: list[str] = []
    start_line = 1
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        stripped_right = raw_line.rstrip()
        continued = stripped_right.endswith("\\")
        if not parts:
            start_line = line_number
        parts.append(stripped_right[:-1].rstrip() if continued else raw_line)
        if continued:
            continue
        if len(parts) == 1:
            yield start_line, parts[0]
        else:
            yield start_line, " ".join(part.strip() for part in parts)
        parts.clear()
    if parts:
        yield start_line, " ".join(part.strip() for part in parts)


def _numbered_attributes(
    attributes: dict[str, str], prefix: str
) -> tuple[tuple[int, str], ...]:
    matches: list[tuple[int, str]] = []
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    for key, value in attributes.items():
        match = pattern.match(key)
        if match:
            matches.append((int(match.group(1)), value))
    return tuple(sorted(matches))


def _validate_command_text(
    command: CommandLine,
    kind: CommandKind,
    location: SourceLocation,
) -> None:
    if command.body and kind not in BODY_COMMAND_KINDS:
        raise UnexpectedCommandTextError(
            f"{location.path}:{location.line}: 指令 {command.name!r} 不允许行尾正文: "
            f"{command.body!r}"
        )

    name = command.name.casefold()
    declared_text = DECLARED_TEXT_ATTRIBUTES.get(name, frozenset())
    declared_non_text = DECLARED_NON_TEXT_ATTRIBUTES.get(name, frozenset())
    for key, value in command.attributes.items():
        normalized_key = key.casefold()
        if normalized_key in declared_text or normalized_key in declared_non_text:
            continue
        if VISIBLE_CJK.search(value) or SUSPECT_TEXT_ATTRIBUTE.search(normalized_key):
            raise UnexpectedCommandTextError(
                f"{location.path}:{location.line}: 指令 {command.name!r} 的未声明参数 "
                f"{key!r} 疑似包含正文: {value!r}"
            )


class AvgParser:
    def parse(self, text: str, source: Path | str) -> ParseResult:
        result = ParseResult()
        active_references: tuple[str, ...] = ()
        source_text = str(source)

        for line_number, raw_line in _logical_lines(text):
            location = SourceLocation(path=source_text, line=line_number)
            if is_known_trailing_noise(source, raw_line):
                result.excluded_warning_counts["source_noise"] = (
                    result.excluded_warning_counts.get("source_noise", 0) + 1
                )
                continue

            try:
                command = parse_command_line(raw_line)
            except AvgSyntaxError as error:
                raise AvgSyntaxError(f"{source_text}:{line_number}: {error}") from error

            if command is None:
                if raw_line.strip():
                    result.events.append(
                        TextEvent(
                            kind=EventKind.NARRATION,
                            location=location,
                            raw=raw_line,
                            text=normalize_text(raw_line),
                            references=active_references,
                        )
                    )
                continue

            result.command_counts[command.name] = (
                result.command_counts.get(command.name, 0) + 1
            )
            normalized_name = command.name.casefold()
            kind = COMMAND_KINDS.get(normalized_name)
            if kind is None:
                raise UnknownCommandError(
                    f"{source_text}:{line_number}: 未注册的 AVG 指令 {command.name!r}"
                )

            _validate_command_text(command, kind, location)
            events = self._handle(command, kind, location, active_references)
            if normalized_name == "decision":
                active_references = ()
            elif normalized_name == "predicate":
                active_references = events[0].references if events else ()
            result.events.extend(events)
        return result

    def _handle(
        self,
        command: CommandLine,
        kind: CommandKind,
        location: SourceLocation,
        references: tuple[str, ...],
    ) -> list[TextEvent]:
        name = command.name.casefold()

        if kind == CommandKind.CONTROL:
            return []

        if name == "name":
            return self._dialogue_body(
                command,
                location,
                references,
                speaker=_attribute(command.attributes, "name"),
            )

        if name == "multiline":
            if not command.body:
                return []
            return [
                self._event(
                    EventKind.DIALOGUE,
                    command,
                    location,
                    text=command.body,
                    speaker=_attribute(command.attributes, "name"),
                    references=references,
                    continuation=True,
                    continuation_end=_is_true(_attribute(command.attributes, "end")),
                )
            ]

        if name in {"dialog", "popupdialog", "tutorial", "voicewithin"}:
            speaker = (
                _attribute(command.attributes, "name")
                or _attribute(command.attributes, "dialogHead")
                or _attribute(command.attributes, "head")
            )
            return self._dialogue_body(command, location, references, speaker=speaker)

        if name in {"avatarid", "isavatarright"}:
            return self._dialogue_body(command, location, references)

        if kind == CommandKind.SCREEN_ATTRIBUTE:
            text = _attribute(command.attributes, "text")
            if not text:
                return []
            return [
                self._event(
                    EventKind.SCREEN_TEXT,
                    command,
                    location,
                    text=text,
                    references=references,
                )
            ]

        if kind == CommandKind.SCREEN_BODY:
            if not command.body:
                return []
            return [
                self._event(
                    EventKind.SCREEN_TEXT,
                    command,
                    location,
                    text=command.body,
                    references=references,
                )
            ]

        if kind == CommandKind.CHOICE:
            return self._decision_events(command, location)

        if kind == CommandKind.BRANCH:
            branch_references = _split_semicolon(
                _attribute(command.attributes, "references")
            )
            return [
                self._event(
                    EventKind.BRANCH,
                    command,
                    location,
                    references=branch_references,
                )
            ]

        if kind == CommandKind.NARRATION_BODY:
            if not command.body:
                return []
            return [
                self._event(
                    EventKind.NARRATION,
                    command,
                    location,
                    text=command.body,
                    references=references,
                )
            ]

        if kind == CommandKind.METADATA_BODY:
            if not command.body:
                return []
            return [
                self._event(
                    EventKind.METADATA,
                    command,
                    location,
                    text=command.body,
                    references=references,
                )
            ]

        if kind == CommandKind.METADATA_ATTRIBUTE:
            character = _attribute(command.attributes, "char")
            if not character:
                return []
            return [
                self._event(
                    EventKind.METADATA,
                    command,
                    location,
                    text=character,
                    references=references,
                )
            ]

        if kind == CommandKind.UI_HINT:
            hint = _attribute(command.attributes, "hint")
            if not hint:
                return []
            return [
                self._event(
                    EventKind.UI_TEXT,
                    command,
                    location,
                    text=hint,
                    references=references,
                )
            ]

        raise AssertionError(f"指令 {command.name!r} 缺少语义 handler")

    @staticmethod
    def _dialogue_body(
        command: CommandLine,
        location: SourceLocation,
        references: tuple[str, ...],
        *,
        speaker: str | None = None,
    ) -> list[TextEvent]:
        if not command.body:
            return []
        return [
            AvgParser._event(
                EventKind.DIALOGUE,
                command,
                location,
                text=command.body,
                speaker=speaker,
                references=references,
            )
        ]

    def _decision_events(
        self, command: CommandLine, location: SourceLocation
    ) -> list[TextEvent]:
        option_texts = _split_semicolon(_attribute(command.attributes, "options"))
        values = _split_semicolon(_attribute(command.attributes, "values"))
        if not option_texts:
            numbered_options = _numbered_attributes(command.attributes, "option")
            option_texts = tuple(value for _, value in numbered_options)
            numbered_values = dict(_numbered_attributes(command.attributes, "value"))
            values = tuple(
                numbered_values.get(number, str(number))
                for number, _ in numbered_options
            )
        if not option_texts:
            return []

        options = tuple(
            ChoiceOption(
                value=values[index] if index < len(values) else str(index + 1),
                text=normalize_text(text),
            )
            for index, text in enumerate(option_texts)
        )
        return [
            TextEvent(
                kind=EventKind.CHOICE,
                location=location,
                raw=command.raw,
                command=command.name,
                attributes=dict(command.attributes),
                options=options,
            )
        ]

    @staticmethod
    def _event(
        kind: EventKind,
        command: CommandLine,
        location: SourceLocation,
        *,
        text: str = "",
        speaker: str | None = None,
        references: tuple[str, ...] = (),
        continuation: bool = False,
        continuation_end: bool = False,
    ) -> TextEvent:
        return TextEvent(
            kind=kind,
            location=location,
            raw=command.raw,
            command=command.name,
            text=normalize_text(text),
            speaker=speaker,
            attributes=dict(command.attributes),
            references=references,
            continuation=continuation,
            continuation_end=continuation_end,
        )


def iter_visible_events(events: Iterable[TextEvent]) -> Iterable[TextEvent]:
    return (
        event
        for event in events
        if event.kind != EventKind.METADATA and (event.text or event.options)
    )
