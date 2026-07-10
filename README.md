# ark-text-extractor

面向个人阅读和大模型剧情分析的明日方舟文本提取器。

项目将 ArknightsGameData 中的 AVG 脚本解析为语义事件，再渲染为连续阅读用的 TXT 或保留来源与分支信息的 JSONL。解析器只提取可读文本，不尝试还原角色立绘、镜头、声音等演出效果。

## 运行要求

- Python >= 3.12
- [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData) 子模块

```bash
git submodule update --init
python main.py
```

默认按照 `story_review_table.json` 提取 TXT，产物保存在 `output/`。

## 输出格式

同时生成阅读文本和结构化事件：

```bash
python main.py --format txt,jsonl
```

- `txt`：保留原有章节目录和汇总文件，增加博士选项、适用分支及此前遗漏的屏幕文本。
- `jsonl`：逐事件记录章节、关卡、角色、选项、分支、源文件、原始行号、原文与规范化文本。
- `_report_review.json`：记录全部已注册指令的使用次数及已确认的源数据噪声。
- 已人工确认的上游噪声仍会计入 `excluded_warning_counts`，但不会污染正文或产生警告。

互斥剧情会被明确标记：

```text
[博士选项 1] 当然。
[博士选项 2] 我再考虑一下。
[适用选项: 1]
阿米娅: 那我们出发吧。
```

## 提取范围

只提取剧情回顾表中的主线、别传、特别行动记述和干员密录：

```bash
python main.py --scope review
```

提取 `gamedata/story/` 下的全部脚本，包括教程、肉鸽对话和活动任务文本：

```bash
python main.py --scope all --format jsonl
```

全量脚本按原始相对路径写入 `output/all/`。`[uc]info/` 中的梗概文件和上游统计报告不会作为独立剧情重复提取。

## 其他选项

```text
--game-data PATH   指定语言数据目录
--output PATH      指定输出目录
--clean            先清理当前 scope 的旧产物
```

解析器使用显式指令注册表。未注册指令、纯控制指令携带正文、未声明参数疑似包含文本或脚本语法错误都会立即终止提取。
排除项集中维护在 `known_warnings.py`，同时精确匹配源文件相对路径和完整原始行；上游内容发生变化时会自动重新产生警告。

## 解析设计

AVG 参数允许单双引号、转义字符、空值和带逗号的文本，单纯用正则捕获整行容易跨属性误匹配。当前实现采用标准库编写的引号感知扫描器：

1. 词法层拆分指令、属性与行尾正文。
2. 语义层将 `name`、`multiline`、`Decision`、`Predicate`、`Sticker`、`Subtitle`、`animtext`、`spellsticker` 等转换为事件。
3. 渲染层分别生成 TXT 和 JSONL。
4. 全部正文指令和纯演出指令都必须显式注册；未知类型立即报错。

该语法规模较小且不是通用格式，引入第三方解析库仍需维护自定义 grammar，因此目前的标准库扫描器比额外依赖更直接。若上游语法出现嵌套表达式，再考虑引入 Lark 等解析库。

## 代码结构

```text
ark_text_extractor/
├── avg_syntax.py   # 引号感知的指令与属性解析
├── avg_parser.py   # 指令语义及事件生成
├── command_registry.py # 全量指令类型与正文策略注册表
├── config.py       # 无副作用配置
├── domain.py       # 剧情、关卡和事件模型
├── game_data.py    # 索引及源文件加载
├── known_warnings.py # 经人工确认的上游脚本噪声
├── renderers.py    # TXT、JSONL 渲染
├── pipeline.py     # 确定性提取流程及报告
└── cli.py          # 命令行入口

tests/
├── test_avg_syntax.py
├── test_avg_parser.py
└── test_corpus_audit.py
```

## 验证

```bash
python -m unittest discover -v
python -m compileall -q ark_text_extractor
```

语料审计测试会遍历剧情回顾表引用的全部脚本，防止新增数据重新造成 `multiline`、选项或其他正文静默丢失。
