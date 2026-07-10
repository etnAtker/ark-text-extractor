from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

from .domain import Chapter, Stage


def load_chapters(path: Path) -> list[Chapter]:
    with path.open("r", encoding="utf-8") as file:
        raw: Any = json.load(file)
    if not isinstance(raw, dict):
        raise ValueError(f"剧情索引必须是对象: {path}")
    return [
        Chapter.from_dict(str(chapter_id), chapter)
        for chapter_id, chapter in raw.items()
        if isinstance(chapter, dict)
    ]


def resolve_story_path(story_dir: Path, relative_path: str) -> Path:
    relative = Path(f"{relative_path}.txt")
    direct = story_dir / relative
    if direct.is_file():
        return direct

    parts = relative.parts
    if parts and parts[0] == "info":
        info_path = story_dir / Path("[uc]info", *parts[1:])
        if info_path.is_file():
            return info_path
    raise FileNotFoundError(f"找不到剧情源文件: {direct}")


def iter_all_story_stages(story_dir: Path) -> Iterable[tuple[Path, Stage]]:
    info_dir = story_dir / "[uc]info"
    for path in sorted(story_dir.rglob("*.txt")):
        if path.is_relative_to(info_dir) or path.name == "avg_segment_report.txt":
            continue
        relative = path.relative_to(story_dir).with_suffix("")
        relative_text = relative.as_posix()
        yield (
            path,
            Stage(
                storyId=relative_text,
                storyCode="",
                storyName=path.stem,
                storyInfo="",
                storyTxt=relative_text,
                avgTag="",
            ),
        )
