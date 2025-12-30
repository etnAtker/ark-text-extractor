# ark-text-extractor

明日方舟剧情文本提取工具，供个人阅读和大模型分析使用。

如有合理格式需求欢迎提Issue。

## 依赖

- Python >= 3.12
- [Arknights Game Data](https://github.com/Kengxxiao/ArknightsGameData)

## 准备工作

1. 初始化游戏数据子模块：
   ```bash
   git submodule update --init
   ```

## 运行

```bash
python main.py
```

提取的剧情文本将按分类保存在 `output` 目录（默认）下。

## 代码结构

- `main.py`: 程序入口，解析`story_review_table.json`，遍历章节并调用提取逻辑。
- `extractor.py`: 提取游戏文本，解析游戏数据中的文本和对话。
- `models.py`: 数据模型定义，映射原始数据的 JSON 结构。
- `configs.py`: 路径和常量配置。

## 配置说明 (`configs.py`)

- `GAME_DATA_DIR`: 游戏数据根目录，默认为 `./ArknightsGameData/zh_CN`。
- `STORY_REVIEW_TABLE`: 剧情索引表路径。
- `STORY_DIR`: 剧情文本目录。
- `OUTPUT_DIR`: 提取结果输出目录，默认为 `./output`。
