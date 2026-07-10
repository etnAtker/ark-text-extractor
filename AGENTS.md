# AGENTS.md — ark-text-extractor

本仓库是一个明日方舟剧情文本提取工具，用途为个人阅读与大模型分析。

Agent 在本仓库中承担两类职责：
1. **提取器开发**：编写 / 维护 Python 提取代码
2. **剧情分析**：基于 `output/` 中的提取结果进行明日方舟剧情研究

---

## 一、仓库结构总览

```
.
├── main.py              # 兼容入口，转发至包内 CLI
├── ark_text_extractor/  # 提取器实现
│   ├── avg_syntax.py    # AVG 指令与属性的词法解析
│   ├── avg_parser.py    # 指令语义与文本事件生成
│   ├── command_registry.py # 全量指令及正文策略注册表
│   ├── domain.py        # Chapter、Stage 与事件模型
│   ├── game_data.py     # 游戏索引及源文件加载
│   ├── known_warnings.py # 已人工确认的上游脚本噪声
│   ├── renderers.py     # TXT / JSONL 渲染
│   ├── pipeline.py      # 提取流程与覆盖率报告
│   ├── config.py        # 无副作用路径配置
│   └── cli.py           # 命令行参数
├── tests/               # 单元测试与全语料审计
├── ArknightsGameData/   # Git 子模块，游戏原始数据（zh_CN）
└── output/              # 提取产物（已加入 .gitignore）
    ├── activity/        # 别传
    ├── mini/            # 特别行动记述
    ├── main/            # 主线剧情
    └── other/           # 干员密录
```

---

## 二、任务一：提取器开发

### 2.1 数据模型（`ark_text_extractor/domain.py`）

- **`StoryType`**（StrEnum）：剧情分类枚举
  - `ACTIVITY` — 别传 → `output/activity/`
  - `MINI_ACTIVITY` — 特别行动记述 → `output/mini/`
  - `MAINLINE` — 主线剧情 → `output/main/`
  - `NONE` — 干员密录 → `output/other/`
- **`Chapter`**：章节，包含 `id`、`name`、`entryType: StoryType`、`infoUnlockDatas: list[Stage]`
- **`Stage`**：单个剧情节点，包含 `storyId`、`storyCode`、`storyName`、`storyInfo`、`storyTxt`、`avgTag`、`storySort`
- **`TextEvent`**：解析后的语义事件，保存类型、正文、角色、选项、分支、源文件与行号

### 2.2 提取流程

1. `main.py` 读取 `STORY_REVIEW_TABLE`（`story_review_table.json`），解析为 `list[Chapter]`
2. `avg_syntax.py` 以引号感知扫描器解析指令、参数与行尾正文，不使用整行贪婪正则
3. `avg_parser.py` 将 `[name]`、`[multiline]`、`[Decision]`、`[Predicate]`、`[Sticker]`、`[Subtitle]`、`[animtext]`、`[spellsticker]` 等转换为语义事件
4. `pipeline.py` 按 `StoryType` 分类、按 `storySort` 排序并生成章节文件；默认兼容原 TXT 路径，也可生成 JSONL
5. 所有正文和纯演出指令都必须登记在 `command_registry.py`；未知指令或未声明文本必须立即报错
6. 已确认的源数据噪声只能用“相对路径 + 完整原始行”加入 `known_warnings.py`，禁止使用宽泛正文规则

### 2.3 路径配置（`ark_text_extractor/config.py`）

| 变量 | 路径 |
|---|---|
| `Settings.game_data_dir` | `./ArknightsGameData/zh_CN` |
| `Settings.story_review_table` | `gamedata/excel/story_review_table.json` |
| `Settings.story_dir` | `gamedata/story/` |
| `Settings.output_dir` | `./output` |

### 2.4 开发规范

- Python >= 3.12，无第三方依赖（仅标准库）
- 使用 `uv` 管理虚拟环境（`.venv/`）
- 类型注解使用 Python 3.12+ 语法（`list[...]`、`dict[...]`）
- 数据模型使用 `@dataclass`，字段名与游戏 JSON key 保持一致
- 文件名经 `sanitize_filename()` 清洗非法字符
- 修改代码后运行 `python -m unittest discover -v` 和 `python main.py` 验证
- 新增正文承载指令时必须同步增加单元测试及全语料覆盖断言

---

## 三、任务二：剧情分析

### 3.1 数据位置

所有提取后的剧情文本位于 `output/` 目录，按类型分为四个子目录：

| 目录 | 内容 | 数量级 |
|---|---|---|
| `output/main/` | 主线剧情（按章节文件夹组织） | ~17 章 |
| `output/activity/` | 别传（按活动文件夹组织） | ~50 个活动 |
| `output/mini/` | 特别行动记述 | ~20 个 |
| `output/other/` | 干员密录（扁平结构） | ~370 个文件 |

### 3.2 单文件格式

每个 `.txt` 文件结构如下：

```
# {StoryType} / {ChapterName} / {StoryCode} {StoryName} / {avgTag}

--- 故事梗概 ---

{storyInfo 梗概文本，可能为"<无文本>"}

--- 对话文本 ---

{角色名}: {台词}
{旁白/描述文本}

--- END ---
```

### 3.3 剧情分析注意事项

- **主线剧情**的文件夹名带有序号前缀（`00_`、`01_`...），反映剧情时间线
- **别传**和**特别行动记述**同样带序号，但序号不严格代表时间线
- **干员密录**为扁平结构，一个干员的多段故事通过文件名序号区分（如 `003_鲜花香水_01.txt`、`003_鲜花香水_02.txt`）
- 对话中 `Dr.{@nickname}` 为玩家角色占位符
- 每个章节文件夹内的 `00_*.txt` 是该章节全部对话的汇总文件
- 梗概（`--- 故事梗概 ---`）部分有时为 `<无文本>`，此时需依赖对话文本分析

### 3.4 分析规范

- **结论必须有原文本支撑**：每条论断必须附带具体的对话原文（含角色名与台词），不得凭印象或记忆得出结论
- **梗概不可靠，禁止作为依据**：故事梗概（`--- 故事梗概 ---` 区域）经过压缩，可能丢失细节或产生偏差；所有论据必须出自 `--- 对话文本 ---` 区域的原始对话
- **论据须覆盖全库**：分析应基于整个游戏文本库（`output/` 全部四个子目录）进行交叉验证，不得仅围绕某个角色的重点章节得出结论

### 3.5 分析建议

- 关注角色名变化与阵营归属，可用于角色关系分析
- 别传往往补充主线未详述的事件，可交叉引用
- 干员密录侧重个人背景故事，适合角色深度分析
