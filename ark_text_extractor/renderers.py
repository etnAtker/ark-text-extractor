from dataclasses import asdict
import json
from typing import Any

from .domain import EventKind, ParsedStage, TextEvent


def render_events_text(
    events: list[TextEvent], *, include_metadata: bool = False
) -> str:
    lines: list[str] = []
    for event in events:
        if event.kind == EventKind.METADATA:
            if include_metadata and event.text:
                lines.append(f"[源标题] {event.text}")
        elif event.kind == EventKind.CHOICE:
            lines.extend(
                f"[博士选项 {option.value}] {option.text}" for option in event.options
            )
        elif event.kind == EventKind.BRANCH:
            if event.references:
                lines.append(f"[适用选项: {', '.join(event.references)}]")
            else:
                lines.append("[分支汇合]")
        elif event.kind == EventKind.DIALOGUE:
            if event.text:
                lines.append(
                    f"{event.speaker}: {event.text}" if event.speaker else event.text
                )
        elif event.kind == EventKind.UI_TEXT:
            if event.text:
                lines.append(f"[界面提示] {event.text}")
        elif event.text:
            lines.append(event.text)
    return "\n".join(lines).strip()


def stage_title(parsed: ParsedStage) -> str:
    chapter = parsed.chapter
    stage = parsed.stage
    title = f"{chapter.entryType.text} / {chapter.name}"
    if stage.storyCode:
        title += f" / {stage.storyCode} {stage.storyName}"
    elif stage.storyName != chapter.name:
        title += f" / {stage.storyName}"
    if stage.avgTag:
        title += f" / {stage.avgTag}"
    return title


def render_stage_text(parsed: ParsedStage) -> str:
    dialog = render_events_text(parsed.result.events) or "<无对话>"
    return (
        f"# {stage_title(parsed)}\n\n"
        f"--- 故事梗概 ---\n\n{parsed.overview}\n\n"
        f"--- 对话文本 ---\n\n{dialog}\n\n"
        "--- END ---\n"
    )


def event_record(parsed: ParsedStage, event: TextEvent) -> dict[str, Any]:
    return {
        "chapter": {
            "id": parsed.chapter.id,
            "name": parsed.chapter.name,
            "type": parsed.chapter.entryType.value,
        },
        "stage": {
            "id": parsed.stage.storyId,
            "code": parsed.stage.storyCode,
            "name": parsed.stage.storyName,
            "tag": parsed.stage.avgTag,
            "sort": parsed.stage.storySort,
        },
        "event": asdict(event),
    }


def render_stage_jsonl(parsed: ParsedStage) -> str:
    records: list[dict[str, Any]] = [
        {
            "chapter": {
                "id": parsed.chapter.id,
                "name": parsed.chapter.name,
                "type": parsed.chapter.entryType.value,
            },
            "stage": {
                "id": parsed.stage.storyId,
                "code": parsed.stage.storyCode,
                "name": parsed.stage.storyName,
                "tag": parsed.stage.avgTag,
                "sort": parsed.stage.storySort,
            },
            "event": {
                "kind": "overview",
                "text": parsed.overview,
                "source": str(parsed.overview_path) if parsed.overview_path else None,
            },
        }
    ]
    records.extend(event_record(parsed, event) for event in parsed.result.events)
    return (
        "\n".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
            for record in records
        )
        + "\n"
    )
