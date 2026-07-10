from collections import Counter
import unittest

from ark_text_extractor.avg_parser import AvgParser
from ark_text_extractor.config import Settings
from ark_text_extractor.command_registry import REGISTERED_COMMANDS
from ark_text_extractor.domain import EventKind
from ark_text_extractor.game_data import (
    iter_all_story_stages,
    load_chapters,
    resolve_story_path,
)


class CorpusAuditTests(unittest.TestCase):
    def test_review_corpus_has_expected_text_coverage(self) -> None:
        settings = Settings()
        if not settings.story_review_table.is_file():
            self.skipTest("未初始化 ArknightsGameData 子模块")

        parser = AvgParser()
        commands: Counter[str] = Counter()
        event_kinds: Counter[EventKind] = Counter()
        choices = 0
        excluded_warnings = 0
        stages = 0

        for chapter in load_chapters(settings.story_review_table):
            for stage in chapter.infoUnlockDatas:
                path = resolve_story_path(settings.story_dir, stage.storyTxt)
                result = parser.parse(path.read_text(encoding="utf-8"), path)
                stages += 1
                commands.update(result.command_counts)
                event_kinds.update(event.kind for event in result.events)
                choices += sum(len(event.options) for event in result.events)
                excluded_warnings += sum(result.excluded_warning_counts.values())

        self.assertGreaterEqual(stages, 1_900)
        self.assertGreaterEqual(commands["multiline"], 1_700)
        self.assertGreaterEqual(event_kinds[EventKind.DIALOGUE], 350_000)
        self.assertGreaterEqual(choices, 6_500)
        self.assertEqual(excluded_warnings, 48)

    def test_all_corpus_commands_are_registered_and_text_is_classified(self) -> None:
        settings = Settings()
        if not settings.story_dir.is_dir():
            self.skipTest("未初始化 ArknightsGameData 子模块")

        parser = AvgParser()
        stages = 0
        anonymous_texts = 0
        dividers = 0
        observed_commands: set[str] = set()
        for path, _ in iter_all_story_stages(settings.story_dir):
            result = parser.parse(path.read_text(encoding="utf-8"), path)
            stages += 1
            observed_commands.update(
                command.casefold() for command in result.command_counts
            )
            anonymous_texts += sum(
                1
                for event in result.events
                if event.command
                and event.command.casefold() in {"avatarid", "isavatarright"}
            )
            dividers += sum(
                1
                for event in result.events
                if event.command and event.command.casefold() == "div" and event.text
            )

        self.assertGreaterEqual(stages, 3_600)
        self.assertEqual(anonymous_texts, 15)
        self.assertEqual(dividers, 24)
        self.assertEqual(observed_commands, REGISTERED_COMMANDS)


if __name__ == "__main__":
    unittest.main()
