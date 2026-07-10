from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class StoryType(StrEnum):
    ACTIVITY = "ACTIVITY"
    MINI_ACTIVITY = "MINI_ACTIVITY"
    MAINLINE = "MAINLINE"
    NONE = "NONE"
    ALL = "ALL"

    @property
    def text(self) -> str:
        return {
            StoryType.ACTIVITY: "别传",
            StoryType.MINI_ACTIVITY: "特别行动记述",
            StoryType.MAINLINE: "主线剧情",
            StoryType.NONE: "干员密录",
            StoryType.ALL: "其他脚本",
        }[self]

    @property
    def output_subdir(self) -> str:
        return {
            StoryType.ACTIVITY: "activity",
            StoryType.MINI_ACTIVITY: "mini",
            StoryType.MAINLINE: "main",
            StoryType.NONE: "other",
            StoryType.ALL: "all",
        }[self]


@dataclass(frozen=True, slots=True)
class Stage:
    storyId: str
    storyCode: str
    storyName: str
    storyInfo: str
    storyTxt: str
    avgTag: str
    storySort: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Stage":
        return cls(
            storyId=str(data["storyId"]),
            storyCode=str(data.get("storyCode") or ""),
            storyName=str(data.get("storyName") or ""),
            storyInfo=str(data.get("storyInfo") or ""),
            storyTxt=str(data["storyTxt"]),
            avgTag=str(data.get("avgTag") or ""),
            storySort=int(data.get("storySort") or 0),
        )


@dataclass(frozen=True, slots=True)
class Chapter:
    id: str
    name: str
    entryType: StoryType
    infoUnlockDatas: tuple[Stage, ...]

    @classmethod
    def from_dict(cls, chapter_id: str, data: dict[str, Any]) -> "Chapter":
        stages = tuple(
            sorted(
                (Stage.from_dict(item) for item in data["infoUnlockDatas"]),
                key=lambda stage: stage.storySort,
            )
        )
        return cls(
            id=str(data.get("id") or chapter_id),
            name=str(data["name"]),
            entryType=StoryType(data["entryType"]),
            infoUnlockDatas=stages,
        )


class EventKind(StrEnum):
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    SCREEN_TEXT = "screen_text"
    CHOICE = "choice"
    BRANCH = "branch"
    METADATA = "metadata"
    UI_TEXT = "ui_text"


@dataclass(frozen=True, slots=True)
class SourceLocation:
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class ChoiceOption:
    value: str
    text: str


@dataclass(frozen=True, slots=True)
class TextEvent:
    kind: EventKind
    location: SourceLocation
    raw: str
    command: str | None = None
    text: str = ""
    speaker: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    options: tuple[ChoiceOption, ...] = ()
    references: tuple[str, ...] = ()
    continuation: bool = False
    continuation_end: bool = False


@dataclass(slots=True)
class ParseResult:
    events: list[TextEvent] = field(default_factory=list)
    command_counts: dict[str, int] = field(default_factory=dict)
    excluded_warning_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedStage:
    chapter: Chapter
    stage: Stage
    overview: str
    overview_path: Path | None
    dialog_path: Path
    result: ParseResult
