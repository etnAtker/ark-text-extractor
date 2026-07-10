from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import shutil

from .avg_parser import AvgParser
from .config import Settings
from .domain import Chapter, ParseResult, ParsedStage, Stage, StoryType
from .game_data import iter_all_story_stages, load_chapters, resolve_story_path
from .renderers import render_stage_jsonl, render_stage_text


INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*]')


def sanitize_filename(name: str) -> str:
    return INVALID_FILENAME_CHARACTERS.sub("_", name)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


@dataclass(slots=True)
class ExtractionReport:
    scope: str
    stages: int = 0
    events: int = 0
    files_written: int = 0
    command_counts: Counter[str] = field(default_factory=Counter)
    excluded_warning_counts: Counter[str] = field(default_factory=Counter)

    def add(self, result: ParseResult) -> None:
        self.stages += 1
        self.events += len(result.events)
        self.command_counts.update(result.command_counts)
        self.excluded_warning_counts.update(result.excluded_warning_counts)

    def to_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "stages": self.stages,
            "events": self.events,
            "files_written": self.files_written,
            "command_counts": dict(self.command_counts.most_common()),
            "excluded_warning_counts": dict(self.excluded_warning_counts.most_common()),
        }


class Extractor:
    def __init__(
        self,
        settings: Settings,
        *,
        formats: set[str] | None = None,
        clean: bool = False,
    ) -> None:
        self.settings = settings
        self.formats = formats or {"txt"}
        invalid_formats = self.formats - {"txt", "jsonl"}
        if invalid_formats:
            raise ValueError(f"不支持的输出格式: {', '.join(sorted(invalid_formats))}")
        self.parser = AvgParser()
        self.clean = clean

    def run(self, scope: str = "review") -> ExtractionReport:
        if scope not in {"review", "all"}:
            raise ValueError(f"不支持的提取范围: {scope}")
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)
        if self.clean:
            self._clean_scope(scope)

        report = self._extract_review() if scope == "review" else self._extract_all()
        report_path = self.settings.output_dir / f"_report_{scope}.json"
        report.files_written += 1
        _write_text(
            report_path,
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )
        return report

    def _clean_scope(self, scope: str) -> None:
        subdirectories = (
            ("activity", "mini", "main", "other") if scope == "review" else ("all",)
        )
        for subdirectory in subdirectories:
            path = self.settings.output_dir / subdirectory
            if path.exists():
                shutil.rmtree(path)

    def _parse_stage(self, chapter: Chapter, stage: Stage) -> ParsedStage:
        dialog_path = resolve_story_path(self.settings.story_dir, stage.storyTxt)
        dialog = dialog_path.read_text(encoding="utf-8").strip()
        overview_path: Path | None = None
        overview = "<无文本>"
        if stage.storyInfo:
            overview_path = resolve_story_path(self.settings.story_dir, stage.storyInfo)
            overview = overview_path.read_text(encoding="utf-8").strip()
        return ParsedStage(
            chapter=chapter,
            stage=stage,
            overview=overview,
            overview_path=overview_path,
            dialog_path=dialog_path,
            result=self.parser.parse(dialog, dialog_path),
        )

    def _extract_review(self) -> ExtractionReport:
        chapters = load_chapters(self.settings.story_review_table)
        report = ExtractionReport(scope="review")
        indexes = {
            StoryType.ACTIVITY: 1,
            StoryType.MINI_ACTIVITY: 1,
            StoryType.MAINLINE: 0,
            StoryType.NONE: 1,
        }
        other_chapters: list[Chapter] = []

        for chapter in chapters:
            if chapter.entryType == StoryType.NONE:
                other_chapters.append(chapter)
                continue
            chapter_index = indexes[chapter.entryType]
            indexes[chapter.entryType] += 1
            self._extract_chapter(chapter, chapter_index, report)

        for chapter in other_chapters:
            chapter_index = indexes[StoryType.NONE]
            indexes[StoryType.NONE] += 1
            self._extract_other(chapter, chapter_index, report)
        return report

    def _extract_chapter(
        self, chapter: Chapter, chapter_index: int, report: ExtractionReport
    ) -> None:
        folder_name = sanitize_filename(f"{chapter_index:02d}_{chapter.name}")
        output_folder = (
            self.settings.output_dir / chapter.entryType.output_subdir / folder_name
        )
        aggregate_text: list[str] = []
        aggregate_jsonl: list[str] = []

        for stage_index, stage in enumerate(chapter.infoUnlockDatas, 1):
            parsed = self._parse_stage(chapter, stage)
            report.add(parsed.result)
            base_name = self._normal_stage_name(stage_index, stage)
            if "txt" in self.formats:
                rendered = render_stage_text(parsed)
                _write_text(output_folder / f"{base_name}.txt", rendered)
                aggregate_text.append(rendered.rstrip())
                report.files_written += 1
            if "jsonl" in self.formats:
                rendered_jsonl = render_stage_jsonl(parsed)
                _write_text(output_folder / f"{base_name}.jsonl", rendered_jsonl)
                aggregate_jsonl.append(rendered_jsonl.rstrip())
                report.files_written += 1

        chapter_name = f"00_{sanitize_filename(chapter.name)}"
        if aggregate_text:
            _write_text(
                output_folder / f"{chapter_name}.txt",
                "\n\n".join(aggregate_text) + "\n",
            )
            report.files_written += 1
        if aggregate_jsonl:
            _write_text(
                output_folder / f"{chapter_name}.jsonl",
                "\n".join(aggregate_jsonl) + "\n",
            )
            report.files_written += 1

    def _extract_other(
        self, chapter: Chapter, chapter_index: int, report: ExtractionReport
    ) -> None:
        base = sanitize_filename(f"{chapter_index:03d}_{chapter.name}")
        multiple = len(chapter.infoUnlockDatas) > 1
        output_folder = self.settings.output_dir / StoryType.NONE.output_subdir
        for index, stage in enumerate(chapter.infoUnlockDatas, 1):
            parsed = self._parse_stage(chapter, stage)
            report.add(parsed.result)
            filename = f"{base}_{index:02d}" if multiple else base
            if "txt" in self.formats:
                _write_text(
                    output_folder / f"{filename}.txt", render_stage_text(parsed)
                )
                report.files_written += 1
            if "jsonl" in self.formats:
                _write_text(
                    output_folder / f"{filename}.jsonl", render_stage_jsonl(parsed)
                )
                report.files_written += 1

    def _extract_all(self) -> ExtractionReport:
        report = ExtractionReport(scope="all")
        output_root = self.settings.output_dir / StoryType.ALL.output_subdir
        for source_path, stage in iter_all_story_stages(self.settings.story_dir):
            relative = source_path.relative_to(self.settings.story_dir)
            chapter = Chapter(
                id=relative.parent.as_posix(),
                name=relative.parent.as_posix(),
                entryType=StoryType.ALL,
                infoUnlockDatas=(stage,),
            )
            parsed = self._parse_stage(chapter, stage)
            report.add(parsed.result)
            target = output_root / relative
            if "txt" in self.formats:
                _write_text(target, render_stage_text(parsed))
                report.files_written += 1
            if "jsonl" in self.formats:
                _write_text(target.with_suffix(".jsonl"), render_stage_jsonl(parsed))
                report.files_written += 1
        return report

    @staticmethod
    def _normal_stage_name(index: int, stage: Stage) -> str:
        if stage.storyCode:
            name = f"{index:02d}_{stage.storyCode}_{stage.storyName}_{stage.avgTag}"
        else:
            name = f"{index:02d}_{stage.storyName}_{stage.avgTag}"
        return sanitize_filename(name)
