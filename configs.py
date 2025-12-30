import os
from pathlib import Path

GAME_DATA_DIR = Path('./ArknightsGameData/zh_CN')
STORY_REVIEW_TABLE = GAME_DATA_DIR / 'gamedata/excel/story_review_table.json'
STORY_DIR = GAME_DATA_DIR / 'gamedata/story'

OUTPUT_DIR = Path('./output')
OUTPUT_ACTIVITY = OUTPUT_DIR / 'activity'
OUTPUT_MINI = OUTPUT_DIR / 'mini'
OUTPUT_MAIN = OUTPUT_DIR / 'main'
OUTPUT_OTHER = OUTPUT_DIR / 'other'

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_ACTIVITY, exist_ok=True)
os.makedirs(OUTPUT_MINI, exist_ok=True)
os.makedirs(OUTPUT_MAIN, exist_ok=True)
os.makedirs(OUTPUT_OTHER, exist_ok=True)
