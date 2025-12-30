import os
import json
from pathlib import Path
import re

from extractor import extract_stage
from configs import (
    OUTPUT_OTHER,
    STORY_REVIEW_TABLE,
)
from models import (
    Chapter,
    StoryType,
)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def load_stories(path: Path) -> list[Chapter]:
    with open(path, "r", encoding="utf-8") as f:
        return Chapter.from_raw(json.load(f))


indexes: dict[StoryType, int] = {
    StoryType.ACTIVITY: 1,
    StoryType.MINI_ACTIVITY: 1,
    StoryType.MAINLINE: 0,
    StoryType.NONE: 1,
}


def extract_normal(chapter: Chapter):
    folder_name = sanitize_filename(f"{indexes[chapter.entryType]:02d}_{chapter.name}")
    indexes[chapter.entryType] += 1
    to_folder = chapter.entryType.save_dir / folder_name
    os.makedirs(to_folder, exist_ok=True)

    stage_index = 1
    text = ""
    for stage in chapter.infoUnlockDatas:
        if stage.storyCode:
            filename = sanitize_filename(
                f"{stage_index:02d}_{stage.storyCode}_{stage.storyName}_{stage.avgTag}.txt"
            )
        else:
            filename = sanitize_filename(
                f"{stage_index:02d}_{stage.storyName}_{stage.avgTag}.txt"
            )
        stage_index += 1

        text += extract_stage(chapter, stage, to_folder / filename)
        text += "\n\n"

    chapter_all_file = to_folder / f"00_{sanitize_filename(chapter.name)}.txt"
    with open(chapter_all_file, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")


def extract_other(chapters: list[Chapter]):
    for chapter in chapters:
        filename = sanitize_filename(f"{indexes[StoryType.NONE]:03d}_{chapter.name}")
        indexes[StoryType.NONE] += 1

        if len(chapter.infoUnlockDatas) == 1:
            extract_stage(
                chapter, chapter.infoUnlockDatas[0], OUTPUT_OTHER / f"{filename}.txt"
            )
        else:
            index = 1
            for stage in chapter.infoUnlockDatas:
                extract_stage(
                    chapter, stage, OUTPUT_OTHER / f"{filename}_{index:02d}.txt"
                )
                index += 1


def main():
    stories = load_stories(STORY_REVIEW_TABLE)
    other_chapters: list[Chapter] = []

    for chapter in stories:
        if chapter.entryType == StoryType.ACTIVITY:
            extract_normal(chapter)
        elif chapter.entryType == StoryType.MINI_ACTIVITY:
            extract_normal(chapter)
        elif chapter.entryType == StoryType.MAINLINE:
            extract_normal(chapter)
        else:
            other_chapters.append(chapter)

    extract_other(other_chapters)


if __name__ == "__main__":
    main()
