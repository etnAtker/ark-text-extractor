from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Settings:
    game_data_dir: Path = PROJECT_ROOT / "ArknightsGameData" / "zh_CN"
    output_dir: Path = PROJECT_ROOT / "output"

    @property
    def story_review_table(self) -> Path:
        return self.game_data_dir / "gamedata" / "excel" / "story_review_table.json"

    @property
    def story_dir(self) -> Path:
        return self.game_data_dir / "gamedata" / "story"
