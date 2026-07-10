import unittest

from ark_text_extractor.avg_syntax import AvgSyntaxError, parse_command_line


class ParseCommandLineTests(unittest.TestCase):
    def test_name_command_without_parentheses(self) -> None:
        command = parse_command_line('[name="可露希尔", avatarId="npc_1"]文本，带逗号')

        self.assertIsNotNone(command)
        assert command is not None
        self.assertEqual(command.name, "name")
        self.assertEqual(command.attributes["name"], "可露希尔")
        self.assertEqual(command.attributes["avatarId"], "npc_1")
        self.assertEqual(command.body, "文本，带逗号")

    def test_empty_quoted_value_does_not_consume_following_attributes(self) -> None:
        command = parse_command_line('[Subtitle(text="", x=300, alignment="center")]')

        assert command is not None
        self.assertEqual(command.attributes["text"], "")
        self.assertEqual(command.attributes["alignment"], "center")

    def test_quoted_commas_and_escaped_quotes(self) -> None:
        command = parse_command_line(
            r'[Subtitle(text="他说：\"走吧，博士。\"", x=300)]'
        )

        assert command is not None
        self.assertEqual(command.attributes["text"], '他说："走吧，博士。"')

    def test_namespaced_command(self) -> None:
        command = parse_command_line('[Battle.AutoChessOnlyAllow(hint="请先完成教程")]')

        assert command is not None
        self.assertEqual(command.name, "Battle.AutoChessOnlyAllow")
        self.assertEqual(command.attributes["hint"], "请先完成教程")

    def test_unclosed_command_is_rejected(self) -> None:
        with self.assertRaises(AvgSyntaxError):
            parse_command_line('[name="阿米娅"')


if __name__ == "__main__":
    unittest.main()
