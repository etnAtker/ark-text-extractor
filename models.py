from dataclasses import fields
from enum import StrEnum
from dataclasses import dataclass
from pathlib import Path

from configs import (
    OUTPUT_ACTIVITY,
    OUTPUT_MINI,
    OUTPUT_MAIN,
    OUTPUT_OTHER,
)


stage_fields = set()
chapter_fields = set()


class StoryType(StrEnum):
    def __new__(cls, wire: str, text: str, save_dir: Path):
        obj = str.__new__(cls, wire)
        obj._value_ = wire
        obj.text = text
        obj.save_dir = save_dir
        return obj

    ACTIVITY = "ACTIVITY", "别传", OUTPUT_ACTIVITY
    MINI_ACTIVITY = "MINI_ACTIVITY", "特别行动记述", OUTPUT_MINI
    MAINLINE = "MAINLINE", "主线剧情", OUTPUT_MAIN
    NONE = "NONE", "干员密录", OUTPUT_OTHER

    text: str
    save_dir: Path


@dataclass
class Stage:
    storyId: str
    storyCode: str
    storyName: str
    storyInfo: str
    storyTxt: str
    avgTag: str

    @classmethod
    def from_dict(cls, data: dict) -> "Stage":
        ret = cls(**{k: v for k, v in data.items() if k in stage_fields})
        if ret.storyInfo:
            ret.storyInfo = ret.storyInfo.replace("info", "[uc]info")
        return ret


@dataclass
class Chapter:
    id: str
    name: str
    entryType: StoryType
    infoUnlockDatas: list[Stage]

    @classmethod
    def from_raw(cls, data: dict[str, dict]) -> list["Chapter"]:
        ret: list["Chapter"] = []
        for _, v in data.items():
            params = {k1: v1 for k1, v1 in v.items() if k1 in chapter_fields}
            ret.append(
                cls(
                    **(
                        params
                        | {
                            "entryType": StoryType(v["entryType"]),
                            "infoUnlockDatas": [
                                Stage.from_dict(d) for d in v["infoUnlockDatas"]
                            ],
                        }
                    )
                )
            )
        return ret


chapter_fields.update({f.name for f in fields(Chapter)})
stage_fields.update({f.name for f in fields(Stage)})
