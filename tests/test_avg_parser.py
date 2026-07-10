import unittest

from ark_text_extractor.avg_parser import (
    AvgParser,
    UnexpectedCommandTextError,
    UnknownCommandError,
    normalize_text,
)
from ark_text_extractor.domain import EventKind
from ark_text_extractor.renderers import render_events_text


class AvgParserTests(unittest.TestCase):
    def test_normalization_removes_style_but_keeps_literal_angle_names(self) -> None:
        text = normalize_text("<i>强调</i>，获得<清香花束>。")

        self.assertEqual(text, "强调，获得<清香花束>。")

    def test_text_bearing_commands_and_branches_are_preserved(self) -> None:
        source = "\n".join(
            (
                '[name="阿米娅"]博士。',
                '[multiline(name="阿米娅")]第一段，',
                '[multiline(name="阿米娅", end=true)]第二段。',
                '[Decision(options="回答一;回答二", values="1;2")]',
                '[Predicate(references="2")]',
                '[name="凯尔希"]这是第二个回答对应的内容。',
                '[Sticker(text="第一行\\n第二行")]',
                '[animtext(id="at1")]<p=1>伦蒂尼姆</><p=2>上午九时</>',
                '[spellsticker(id="s1")]<p=1>声音，归来。</>',
            )
        )

        result = AvgParser().parse(source, "fixture.txt")

        self.assertEqual(result.events[0].speaker, "阿米娅")
        choices = [event for event in result.events if event.kind == EventKind.CHOICE]
        self.assertEqual(
            [option.text for option in choices[0].options], ["回答一", "回答二"]
        )
        branch_dialogue = next(
            event
            for event in result.events
            if event.text == "这是第二个回答对应的内容。"
        )
        self.assertEqual(branch_dialogue.references, ("2",))
        rendered = render_events_text(result.events)
        self.assertIn("[博士选项 1] 回答一", rendered)
        self.assertIn("[适用选项: 2]", rendered)
        self.assertIn("伦蒂尼姆\n上午九时", rendered)
        self.assertIn("声音，归来。", rendered)

    def test_unknown_command_always_fails(self) -> None:
        with self.assertRaises(UnknownCommandError):
            AvgParser().parse("[FutureCommand(foo=1)]", "fixture.txt")

    def test_control_command_with_body_fails(self) -> None:
        with self.assertRaises(UnexpectedCommandTextError):
            AvgParser().parse("[Character]不能忽略的正文", "fixture.txt")

    def test_undeclared_text_attribute_fails(self) -> None:
        with self.assertRaises(UnexpectedCommandTextError):
            AvgParser().parse('[Character(caption="不能忽略的正文")]', "fixture.txt")

    def test_known_noise_requires_exact_source_and_raw_line(self) -> None:
        raw = '[charslot(slot="r",name="avg_4087_ines_1#1$1",focus="r")]已改'
        source = "/game/zh_CN/gamedata/story/obt/main/level_main_12-17_end.txt"

        excluded = AvgParser().parse(raw, source)
        with self.assertRaises(UnexpectedCommandTextError):
            AvgParser().parse(raw, "/game/gamedata/story/other.txt")

        self.assertFalse(excluded.events)
        self.assertEqual(excluded.excluded_warning_counts, {"source_noise": 1})

    def test_empty_subtitle_is_ignored(self) -> None:
        result = AvgParser().parse(
            '[Subtitle(text="", x=300, alignment="center")]', "fixture.txt"
        )

        self.assertFalse(result.events)

    def test_numbered_decision_schema(self) -> None:
        result = AvgParser().parse(
            '[decision(option1="是", value1="yes", option2="否", value2="no")]',
            "fixture.txt",
        )

        options = result.events[0].options
        self.assertEqual(
            [(item.value, item.text) for item in options], [("yes", "是"), ("no", "否")]
        )

    def test_anonymous_dialogue_and_divider_body_are_preserved(self) -> None:
        result = AvgParser().parse(
            "[isAvatarRight=false]系统文本\n[Div] Part.01", "fixture.txt"
        )

        self.assertEqual(
            [event.text for event in result.events], ["系统文本", "Part.01"]
        )

    def test_backslash_continued_command_keeps_starting_line(self) -> None:
        source = "\n".join(
            (
                "空行后的说明",
                "[Tutorial(focusX=30, \\",
                'dialogHead="$avatar_amiya")] \\',
                "博士，请点击这里。",
            )
        )

        result = AvgParser().parse(source, "tutorial.txt")

        self.assertEqual(result.events[1].text, "博士，请点击这里。")
        self.assertEqual(result.events[1].speaker, "$avatar_amiya")
        self.assertEqual(result.events[1].location.line, 2)


if __name__ == "__main__":
    unittest.main()
