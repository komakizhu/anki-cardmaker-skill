# Anki Cardmaker Skill

一个面向 Codex 的 Anki 制卡 Skill：把截图、单词表、文本、Markdown 或 PDF 整理成结构化闪卡，先生成 HTML 预览，用户确认后再通过 AnkiConnect 导入 Anki。

An Anki card-making Skill for Codex. It converts screenshots, vocabulary lists, text, Markdown, and PDFs into structured cards, shows a standalone HTML preview first, and syncs to Anki only after explicit approval.

**Version:** `1.5.1`

## Features / 功能

- 自然语言指定题型：词义题、填空题、单选题、多选题、判断题、简答题
- Natural-language routing for vocabulary meaning, cloze, single-choice, multiple-choice, true-false, and short-answer cards
- 说“制卡”“做卡”“闪卡”“Anki”“导入 Anki”等也会触发本 Skill；未指定题型时先询问卡片类型
- Card-making intent such as “制卡”, “flashcards”, “Anki”, or “import to Anki” triggers the Skill; ambiguous requests prompt for a card type first
- 中英文和中英混合表达具有相同触发优先级，例如 `帮我 make vocabulary cards`、`make cloze cards`、`整理成单选题` 都能正常路由
- Chinese, English, and mixed Chinese-English requests have equal routing priority
- 支持斜杠入口：`/anki` 和 `/闪卡`
- Slash entry points: `/anki` and `/闪卡`
- 孤立英文单词表默认生成词义题，不会误判为 Cloze 或普通问答题
- Isolated English word lists default to vocabulary meaning cards, not Cloze or generic Q&A cards
- 英语词汇卡支持词典释义、词性、中文释义、等级、音标、单击播放音频
- Vocabulary cards support dictionary definitions, part of speech, Chinese glosses, exam levels, phonetics, and one-click audio
- 词汇关系：同义词、反义词、近义词、形近词/易混词、固定搭配、词根词缀
- Bilingual examples: at least three contextual examples with aligned Chinese translations
- 其他含义：每个含义配一条例句
- 学习阶段匹配：中考、高考、CET-4/6、TEM-4/8、IELTS、TOEFL、GRE、GMAT、BEC、学术英语、职场英语、考研英语一/二、通用
- 浅色/深色主题、桌面端和 Anki Mobile 适配、衬线体阅读风格
- LaTeX 公式 MathJax 渲染
- 导入前结构校验、HTML 预览、出处状态校验和自动化回归测试

## Type Routing / 题型路由

以下表达会触发本 Skill：`制卡`、`做卡`、`闪卡`、`卡片`、`Anki`、`anki`、`导入 Anki`、`同步到 Anki`，以及 “make cards”, “flashcards”, “import to Anki”。

输入 `/anki` 或 `/闪卡` 后，会先显示中英双语题型菜单：

```text
制卡 / make cards
做卡 / create flashcards
闪卡 / flashcards
导入 Anki / import to Anki
词义题 / vocabulary meaning
填空题 / cloze / fill-in-the-blank
单选题 / single-choice
多选题 / multiple-choice
判断题 / true-or-false
简答题 / short-answer
```

如果没有指定题型，Skill 会先询问：词义题、填空题、单选题、多选题、判断题还是简答题；不会直接猜测并导入。

可以直接用自然语言调用：

| 用户说法 | Routed type |
| --- | --- |
| “把这些单词整理成词义题/单词题” | `vocabulary_meaning` |
| “把这篇完形填空整理成填空题” | `cloze` |
| “整理成单选题” | `single_choice` |
| “整理成多选题” | `multiple_choice` |
| “整理成判断题” | `true_false` |
| “整理成简答题/问答题” | `short_answer` |

### Vocabulary routing rule / 词汇路由规则

以下输入会强制走词义题：

- 截图中是一列互相独立的英文单词
- 用户明确说“单词题”或“词义题”
- 单个英文单词附带例句或释义

只有以下情况才使用 Cloze：

- 用户明确要求填空/Cloze
- 原材料本身是带有真实空缺的文章、练习或完形填空

一个单独的英文单词，即使最终使用 Anki 的 `QA` 笔记模型，也仍然必须使用：

```json
{
  "type": "QA",
  "question_type": "vocabulary_meaning"
}
```

`type: QA` 只表示 Anki 笔记模型，不表示题型是普通问答题。

### Card-Type Sub-skills / 题型子模块

题型规则拆分在 `subskills/` 中；同时提供 6 个可在 Codex Skill 列表中直接选择的同级 Skill。主 Skill 负责通用触发、询问和统一流程：

| Sub-skill | 用途 |
| --- | --- |
| `vocabulary-meaning` | 词义题 / 单词题 |
| `cloze` | 填空题 / 完形填空 |
| `single-choice` | 单选题 |
| `multiple-choice` | 多选题 |
| `true-false` | 判断题 |
| `short-answer` | 简答题 / 问答题 |

所有子模块共享同一套校验、预览、牌组选择、音频、深浅色主题和两阶段导入门禁。

可直接调用的 Skill 名称：

- `anki-cardmaker-vocabulary`
- `anki-cardmaker-cloze`
- `anki-cardmaker-single-choice`
- `anki-cardmaker-multiple-choice`
- `anki-cardmaker-true-false`
- `anki-cardmaker-short-answer`

如果 Codex 已经打开项目目录，重新加载项目或重启 Codex 后，这些同级 Skill 才会出现在调用列表中。

## Learning Stages / 学习阶段

生成英文词汇卡前，Skill 会询问或读取学习阶段，并将阶段传递到例句生成：

- 例句词汇难度
- 句子长度
- 语法复杂度
- 语境和考试场景
- 高频搭配

支持：`中考英语`、`高考英语`、`CET-4`、`CET-6`、`TEM-4`、`TEM-8`、`IELTS`、`TOEFL`、`GRE`、`GMAT`、`BEC`、`学术英语`、`职场英语`、`考研英语一`、`考研英语二`、`通用`。

优先使用真题或权威来源；无法确认出处时，必须明确标记为自拟阶段匹配例句，不得伪造真题来源。

## Vocabulary Card Contract / 词汇卡规范

孤立词汇卡必须包含：

1. 词典释义：单词、词性、中文释义、等级、音标、音频、Oxford/Collins 释义和中文注释
2. 双语例句：至少三条例句，场景不同，中文翻译与英文逐条对应
3. 解读：解释当前语境中的词义
4. 口诀：帮助记忆的联想或记忆钩子
5. 词汇关系：同义、反义、近义、形近/易混、固定搭配、词根词缀
6. 其他含义：每个其他含义都必须有对应例句

### Example provenance / 例句出处

每张孤立词汇卡都必须填写：

```json
{
  "learning_stage": "考研英语二",
  "source_status": "generated",
  "example_sources": [
    "自拟·考研英语二阶段匹配例句",
    "自拟·考研英语二阶段匹配例句",
    "自拟·考研英语二阶段匹配例句"
  ]
}
```

`source_status` 可取：

- `verified`：出处元数据通过格式检查；如果有 URL，可进一步检查链接可达性，但不代表已证明句子确实来自该来源
- `generated`：例句为自拟，出处标签必须以 `自拟·` 开头并带学习阶段
- `needs_review`：出处待确认，禁止预览和导入

## Two-Stage Import Gate / 两阶段导入门禁

所有制卡操作必须分两步完成：

### Stage 1: Build and preview / 制卡并预览

1. 识别题型和学习阶段
2. 生成 JSON 卡片
3. 运行结构校验
4. 生成 HTML 预览
5. 提议 Anki 牌组名称
6. 等待用户确认

### Stage 2: Import after approval / 用户确认后导入

只有用户明确说“确认导入”“同意导入”“导入这个牌组”或 `sync it` 后，才允许调用 AnkiConnect 或运行同步脚本。

“生成”“整理”“做成卡片”“给我看看”都不代表允许导入。

## CLI Workflow / 命令行流程

### Validate / 校验

```bash
python3 scripts/validate_cards.py --file cards.json
```

### Preview / 预览

```bash
python3 scripts/preview_cards.py \
  --file cards.json \
  --output preview.html
```

预览会包含公式 MathJax、词汇卡音频节点和移动端 CSS 契约。音频是否能实际播放还取决于本机语音引擎和生成的媒体文件。

### Verify sources / 核验出处

```bash
python3 scripts/verify_example_sources.py --file cards.json
```

该命令只检查 URL 可达性和出处格式，不会声称完成语义溯源。

### Import / 导入

确认预览和牌组后：

```bash
python3 scripts/anki_sync.py \
  --file cards.json \
  --deck "English Vocabulary"
```

要求：Anki 已打开，并安装、启用 AnkiConnect，默认监听 `127.0.0.1:8765`。

Cloze 默认写入 `Back Extra` 字段；自定义笔记类型可用 `--cloze-extra-field` 覆盖。

## Custom Decks / 自定义牌组

命令行参数优先级最高：

```bash
python3 scripts/anki_sync.py --file cards.json --deck "考研英语二词汇"
```

也可以在 JSON 顶层设置：

```json
{
  "deck": "考研英语二词汇",
  "cards": []
}
```

如果两处都没有设置，默认牌组为 `AnkiCardmaker`。

## Regression Tests / 自动化回归测试

运行项目自带的标准库回归套件：

```bash
python3 scripts/test_regression.py
```

覆盖：

- 单词截图路由到词义题
- Cloze 误判拦截
- 学习阶段传递到例句出处
- 例句与出处一一对应
- 音频播放按钮 HTML 快照
- 手机端布局 CSS/HTML 快照

完整示例校验：

```bash
for file in examples/*.json; do
  python3 scripts/validate_cards.py --file "$file"
done
```

## Project Debug Workflow / 项目内调试流程

项目调试版位于：

```text
.agents/skills/anki-cardmaker/
```

它是唯一源目录。根目录的 `SKILL.md`、`scripts/`、`schemas/`、`examples/` 和 `VERSION` 是发布镜像，不要直接编辑。

修改项目源后同步到根目录：

```bash
python3 .agents/skills/anki-cardmaker/scripts/sync_project_skill.py
python3 .agents/skills/anki-cardmaker/scripts/sync_project_skill.py --check
```

第二条命令必须通过后再提交或发布。

## Repository Layout / 目录结构

```text
.
├── .agents/skills/anki-cardmaker/  # project-local source of truth
├── SKILL.md                        # publish mirror
├── scripts/                        # validation, preview, sync, tests
├── schemas/                        # JSON Schema
├── examples/                       # examples and HTML snapshot contracts
├── subskills/                      # card-type routing profiles
├── skills/                         # publish copies of directly callable sub-skills
├── skills/anki/                    # /anki launcher
├── skills/闪卡/                    # /闪卡 launcher
└── VERSION                         # published version
```

## License

See the repository license file if provided.
