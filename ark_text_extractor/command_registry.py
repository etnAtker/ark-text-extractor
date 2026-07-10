"""AVG 指令注册表。

指令名按大小写不敏感处理。任何未出现在此处的指令都会让解析立即失败；纯控制
指令如果意外携带正文或疑似文本参数，同样会失败。
"""

from enum import StrEnum
import re


class CommandKind(StrEnum):
    CONTROL = "control"
    DIALOGUE_BODY = "dialogue_body"
    NARRATION_BODY = "narration_body"
    SCREEN_BODY = "screen_body"
    SCREEN_ATTRIBUTE = "screen_attribute"
    CHOICE = "choice"
    BRANCH = "branch"
    METADATA_BODY = "metadata_body"
    METADATA_ATTRIBUTE = "metadata_attribute"
    UI_HINT = "ui_hint"


COMMAND_KINDS: dict[str, CommandKind] = {
    "name": CommandKind.DIALOGUE_BODY,
    "multiline": CommandKind.DIALOGUE_BODY,
    "dialog": CommandKind.DIALOGUE_BODY,
    "popupdialog": CommandKind.DIALOGUE_BODY,
    "tutorial": CommandKind.DIALOGUE_BODY,
    "voicewithin": CommandKind.DIALOGUE_BODY,
    "avatarid": CommandKind.DIALOGUE_BODY,
    "isavatarright": CommandKind.DIALOGUE_BODY,
    "narration": CommandKind.NARRATION_BODY,
    "animtext": CommandKind.SCREEN_BODY,
    "spellsticker": CommandKind.SCREEN_BODY,
    "div": CommandKind.SCREEN_BODY,
    "sticker": CommandKind.SCREEN_ATTRIBUTE,
    "subtitle": CommandKind.SCREEN_ATTRIBUTE,
    "decision": CommandKind.CHOICE,
    "predicate": CommandKind.BRANCH,
    "header": CommandKind.METADATA_BODY,
    "title": CommandKind.METADATA_BODY,
    "interlude": CommandKind.METADATA_ATTRIBUTE,
    "battle.autochessonlyallow": CommandKind.UI_HINT,
}


CONTROL_COMMANDS = frozenset(
    {
        "act38d1.focusslot",
        "act38d1.jumptopermanentmap",
        "activity.resettoentry",
        "addfavor",
        "additem",
        "animtextclean",
        "autochess.focusband",
        "autochess.focusstageinfo",
        "autochess.shopdetailfocus",
        "autochess.shoplistfocusdiychess",
        "avgdisplay",
        "background",
        "backgroundtween",
        "battle.autochessonlydisable",
        "battle.delay",
        "battle.elay",
        "battle.ensuremincost",
        "battle.ensureminsp",
        "battle.lockautochesshud",
        "battle.lockfunction",
        "battle.pause",
        "battle.setdragoperationlock",
        "battle.switchtodefaultuistate",
        "battle.unlockautochesshud",
        "battle.unlockfunction",
        "bgeffect",
        "blocker",
        "building.ensureoperationmode",
        "building.focusbroom",
        "building.focusonprivateowner",
        "building.privatereturn",
        "cameraeffect",
        "camerafocusto",
        "camerascale",
        "camerashake",
        "campaign.focuszone",
        "campaign.registerzonebtn",
        "carving.focusbuycard",
        "carving.selectcardslot",
        "carving.selecthandcard",
        "cgitem",
        "chaa",
        "character",
        "characteraction",
        "charactercutin",
        "charselect.applysortfilter",
        "charslot",
        "charslsot",
        "condition",
        "consumeguideonstoryend",
        "cooperatebattle.camerafocusto",
        "cooperatebattle.lockcamera",
        "createeffect",
        "crisisv2.focusslot",
        "crisisv2.hidepreview",
        "crisisv2.resettoentry",
        "crisisv2.switchmap",
        "curtain",
        "dalay",
        "daley",
        "dealy",
        "delat",
        "delau",
        "delay",
        "delay9ti",
        "delay=",
        "delayt",
        "deliveritem",
        "delya",
        "dialo",
        "dialogs",
        "duration",
        "effect",
        "emoji",
        "end",
        "entertouristmode",
        "executeactionarray",
        "fadetime",
        "finisheffect",
        "firework.waitforcraftpagestable",
        "focusout",
        "focusparam",
        "foginview",
        "fognotinview",
        "gacha",
        "gotocharinfo",
        "gotopage",
        "gotostage",
        "gridbg",
        "hidecgitem",
        "hideitem",
        "image",
        "imagerotate",
        "imagetween",
        "imgeffect",
        "inputblocker",
        "interlock.ensuremapstatus",
        "largebg",
        "largebgtween",
        "mixstory.focusstoryline",
        "move",
        "musicvolume",
        "musicvolune",
        "obtain",
        "optionbranch",
        "orderrift",
        "palysound",
        "playanim",
        "playmusic",
        "playsound",
        "resetcamera",
        "sandbox.dungeonfocusnode",
        "sandbox.ensuredungeonstable",
        "sandbox.focusmodule",
        "sandboxbattle.camerafocusto",
        "sandboxbattle.lockcamera",
        "sandboxv2.closegainitempage",
        "sandboxv2.dungeonbacktodungeonstate",
        "sandboxv2.dungeonfocusnode",
        "sandboxv2.ensuredungeonquest",
        "sandboxv2.ensuredungeonstable",
        "sandboxv2.opengainitempage",
        "sandboxv2.settlegameandleave",
        "sandboxv3.dungeonfocusnode",
        "sandboxv3activepredefine",
        "sandboxv3openshop",
        "sandboxv3summontrap",
        "save",
        "setconditionprogress",
        "setposition",
        "shop.switchtoptab",
        "showitem",
        "skipnode",
        "skiptothis",
        "soundvolume",
        "spellstickerclear",
        "startbattle",
        "stickerclear",
        "stopmucis",
        "stopmusic",
        "stopsound",
        "summonenemy",
        "summontrap",
        "theater",
        "timerclear",
        "timersticker",
        "uioperation",
        "verticalbg",
        "video",
        "warp",
        "withdraw",
        "withdrawsource",
    }
)

COMMAND_KINDS.update({command: CommandKind.CONTROL for command in CONTROL_COMMANDS})

REGISTERED_COMMANDS = frozenset(COMMAND_KINDS)

# 参数名看起来可能承载正文时，必须由对应 handler 显式声明或明确标注为资源 ID。
SUSPECT_TEXT_ATTRIBUTE = re.compile(
    r"(?:text|content|caption|option|hint|desc|message|title)", re.IGNORECASE
)

DECLARED_TEXT_ATTRIBUTES: dict[str, frozenset[str]] = {
    "name": frozenset({"name"}),
    "multiline": frozenset({"name"}),
    "sticker": frozenset({"text"}),
    "subtitle": frozenset({"text"}),
    "decision": frozenset({"options", "option1", "option2", "option3", "option4"}),
    "interlude": frozenset({"char"}),
    "battle.autochessonlyallow": frozenset({"hint"}),
}

DECLARED_NON_TEXT_ATTRIBUTES: dict[str, frozenset[str]] = {
    "optionbranch": frozenset({"option0", "option1", "option2"}),
    "delay": frozenset({"title_test"}),
    "popupdialog": frozenset({"dialoghead", "dialogx", "dialogy"}),
    "tutorial": frozenset({"dialoghead", "dialogx", "dialogy"}),
}
