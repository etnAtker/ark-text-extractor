import argparse
from pathlib import Path
from collections.abc import Sequence

from .config import Settings
from .pipeline import Extractor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="提取明日方舟剧情文本")
    parser.add_argument(
        "--game-data",
        type=Path,
        default=Settings().game_data_dir,
        help="ArknightsGameData 的语言数据目录",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Settings().output_dir,
        help="输出目录",
    )
    parser.add_argument(
        "--scope",
        choices=("review", "all"),
        default="review",
        help="review 仅提取剧情回顾表，all 提取全部脚本",
    )
    parser.add_argument(
        "--format",
        default="txt",
        help="输出格式，多个格式以逗号分隔：txt,jsonl",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="提取前清理当前范围的旧产物",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    formats = {item.strip() for item in args.format.split(",") if item.strip()}
    settings = Settings(
        game_data_dir=args.game_data.resolve(),
        output_dir=args.output.resolve(),
    )
    report = Extractor(
        settings,
        formats=formats,
        clean=args.clean,
    ).run(args.scope)
    print(
        f"提取完成：{report.stages} 个脚本，{report.events} 个事件，"
        f"写入 {report.files_written} 个文件，"
        f"排除 {sum(report.excluded_warning_counts.values())} 个已知噪声"
    )
    return 0
