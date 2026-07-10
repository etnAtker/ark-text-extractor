"""经人工核对的上游脚本噪声。

排除项同时匹配剧情源文件相对路径和完整原始行。上游数据只要发生任何变化，
对应内容就会重新进入警告流程，避免宽泛规则误吞未来新增的真实正文。
"""

from pathlib import Path


STORY_PATH_MARKER = "/gamedata/story/"

KNOWN_TRAILING_NOISE = frozenset(
    {
        (
            "activities/act10mini/level_act10mini_st02.txt",
            "[delay(time=2)]]",
        ),
        (
            "activities/act13d5/level_act13d5_08_beg.txt",
            "[Character]]",
        ),
        (
            "activities/act13side/level_act13side_04_end.txt",
            "[character]]",
        ),
        (
            "activities/act13side/level_act13side_07_end.txt",
            "[character]]",
        ),
        (
            "activities/act14side/level_act14side_02_end.txt",
            '[character(name="avg_206_gnosis_1#2$1")]]',
        ),
        (
            "activities/act14side/level_act14side_02_end.txt",
            '[character(name="avg_206_gnosis_1#4$1")]]',
        ),
        (
            "activities/act14side/level_act14side_02_end.txt",
            '[character(name="avg_206_gnosis_1#7$1")]]',
        ),
        (
            "activities/act14side/level_act14side_02_end.txt",
            '[character(name="avg_npc_262_1#7$1")]]',
        ),
        (
            "activities/act14side/level_act14side_02_end.txt",
            '[character(name="avg_npc_262_1#8$1")]]',
        ),
        (
            "activities/act14side/level_act14side_04_beg.txt",
            "[delay(time=2)]]",
        ),
        (
            "activities/act14side/level_act14side_08_end.txt",
            '[Background(image="24_g2_temple_indoor",screenadapt="coverall")]b',
        ),
        (
            "activities/act14side/level_act14side_st02.txt",
            "[delay(time=1.5)]]",
        ),
        (
            "activities/act14side/level_act14side_st02.txt",
            "[delay(time=2)]]",
        ),
        (
            "activities/act15d0/level_act15d0_06_beg.txt",
            '[Character(name="char_108_silent_1#3", name2="char_249_muesys_1#5",focus=1)]。',
        ),
        (
            "activities/act16d5/level_act16d5_05_end.txt",
            "[delay(time=0.51)]]",
        ),
        (
            "activities/act17side/level_act17side_01_end.txt",
            '[Character(name="avg_npc_453_1#1$1",name2="avg_npc_454_1#1$1",focus=2)]。',
        ),
        (
            "activities/act17side/level_act17side_04_end.txt",
            '[Character(name="avg_npc_183#1",name2="avg_npc_448_1#1$1",focus=2)]]',
        ),
        (
            "activities/act17side/level_act17side_05_end.txt",
            '[Character(name="avg_1023_ghost2_1#4$1",name2="char_263_skadi#3",focus=2)].',
        ),
        (
            "activities/act17side/level_act17side_st04.txt",
            '[Character(name="avg_npc_183#1",name2="avg_npc_445_1#1$1",focus=1)]。',
        ),
        (
            "activities/act18d0/level_act18d0_07_beg.txt",
            "[character]]",
        ),
        (
            "activities/act18d3/level_act18d3_02_end.txt",
            "[stopmusic(fadetime=1)]]",
        ),
        (
            "activities/act18d3/level_act18d3_07_end.txt",
            '[Character(name="avg_npc_182#2")]。',
        ),
        (
            "activities/act35side/level_act35side_03_beg.txt",
            '[charslot(slot = "m", name = "avg_4140_lasher_1#1$1")]。',
        ),
        (
            "activities/act38side/level_act38side_st04.txt",
            '[charslot(slot = "l", name = "avg_npc_1541_1#8$1", focus="l")]4',
        ),
        (
            "activities/act3d0/level_act3d0_01_end.txt",
            '[Character(name="char_348_ceylon_4#2",name2="char_145_prove_1",focus=1)]。',
        ),
        (
            "activities/act46side/level_act46side_09_end.txt",
            '[charslot(slot = "m", afrom=1,ato=0, duration = 0.5)]z',
        ),
        (
            "activities/act47side/level_act47side_st01.txt",
            '[charslot(slot="l",focus="l")].',
        ),
        (
            "activities/act49side/level_act49side_07_beg.txt",
            "[charslot]m",
        ),
        (
            "activities/act9mini/level_act9mini_st03.txt",
            "[character]]",
        ),
        (
            "obt/main/level_main_02-09_end.txt",
            '[Character(name="char_010_chen_1", name2="char_012_misa_1", focus=1)]=',
        ),
        (
            "obt/main/level_main_10-04_beg.txt",
            "[delay(time=0.7)]]",
        ),
        (
            "obt/main/level_main_10-14_end.txt",
            '[Background(image="27_g7_subway",screenadapt="coverall")]]',
        ),
        (
            "obt/main/level_main_12-17_end.txt",
            '[charslot(slot="r",name="avg_4087_ines_1#1$1",focus="r")]已改',
        ),
        ("obt/main/level_st_09-01.txt", "[delay(time=1)]]"),
        (
            "obt/memory/story_bibeak_1_1.txt",
            "[Blocker(a=0, r=0, g=0, b=0, fadetime=0, block=true)]d",
        ),
        (
            "obt/memory/story_blackd_2_1.txt",
            '[charslot(slot = "m", name = "avg_198_blackd_1#6$1")]我',
        ),
        (
            "obt/memory/story_bldsk_2_1.txt",
            '[Character(name="avg_171_bldsk_1#1$1",name2="char_002_amiya_1#4",focus=1)]S',
        ),
        (
            "obt/memory/story_blkngt_1_1.txt",
            '[charslot(slot = "M", name = "avg_476_blkngt_1#10$1")]r',
        ),
        (
            "obt/memory/story_fartth_1_1.txt",
            "[CameraShake(duration=0.5, xstrength=30, ystrength=30, vibrato=30, randomness=90, fadeout=true, block=false)]]",
        ),
        (
            "obt/memory/story_franka_1_1.txt",
            "[[character(fadetime=0.3)]]",
        ),
        ("obt/memory/story_gnosis_1_1.txt", "[delay(time=1)],"),
        ("obt/memory/story_cement_1_1.txt", "[]"),
        (
            "obt/memory/story_jesica_1_1.txt",
            '[Character(name="char_259_Jessica_1", name2="char_107_liskam_1",focus=2)].',
        ),
        ("obt/memory/story_malist_1_1.txt", "[delay(time=1)]："),
        ("obt/memory/story_sqrrel_1_1.txt", "[delay(time=1.1)]]"),
    }
)


def story_relative_path(source: Path | str) -> str:
    normalized = str(source).replace("\\", "/")
    if STORY_PATH_MARKER in normalized:
        return normalized.split(STORY_PATH_MARKER, 1)[1]
    return normalized.removeprefix("./")


def is_known_trailing_noise(source: Path | str, raw_line: str) -> bool:
    return (story_relative_path(source), raw_line) in KNOWN_TRAILING_NOISE
