from pathlib import Path
import re

from configs import STORY_DIR
from models import (
    Chapter,
    Stage,
)


def extract_dialog(lines: str):
    raw_lines = lines.split("\n")
    dialog_lines: list[str] = []
    for line in raw_lines:
        if line.strip().startswith("[name="):
            matches = re.search(r"^\[name=\s?[\"'](.*)[\"'].*\]\s?(.*)$", line)
            if not matches:
                raise ValueError(f"Invalid dialog line: {line}")

            name = matches.group(1)
            dialog = matches.group(2).strip()

            if dialog == "":
                continue

            dialog_lines.append(f"{name}: {dialog}\n" if name != "" else f"{dialog}\n")
        elif line.strip().startswith("[Sticker("):
            matches = re.search(r"^\[Sticker.+text\s?=\s?[\"'](.+?)[\"'].*$", line)
            if not matches:
                continue

            chunk = matches.group(1)
            if chunk == "":
                continue

            chunk = chunk[2:] if chunk.startswith(r"\n") else chunk
            chunk = chunk[:-2] if chunk.endswith(r"\n") else chunk

            dialog_lines.append(chunk.replace(r"\n", "\n") + "\n")
        elif not line.strip().startswith("["):
            dialog_lines.append(line + "\n")

    return "".join(dialog_lines).strip()


def extract_stage(chapter: Chapter, stage: Stage, to: Path):
    title = f"{chapter.entryType.text} / {chapter.name}"
    if stage.storyCode:
        title += f" / {stage.storyCode} {stage.storyName}"
    elif stage.storyName != chapter.name:
        title += f" / {stage.storyName}"

    if stage.avgTag and stage.avgTag != "":
        title += f" / {stage.avgTag}"

    if stage.storyInfo:
        overview = (
            (STORY_DIR / f"{stage.storyInfo}.txt").read_text(encoding="utf-8").strip()
        )
    else:
        overview = "<无文本>"

    dialog = (STORY_DIR / f"{stage.storyTxt}.txt").read_text(encoding="utf-8").strip()
    dialog = extract_dialog(dialog)
    if dialog == "":
        dialog = "<无对话>"

    text = ""
    text += f"# {title}"
    text += "\n\n--- 故事梗概 ---\n\n"
    text += overview
    text += "\n\n--- 对话文本 ---\n\n"
    text += dialog
    text += "\n\n--- END ---\n"

    with open(to, "w", encoding="utf-8") as f:
        f.write(text)

    return text
