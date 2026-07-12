# Anki Cardmaker Skill

Anki 卡片制作 Skill，支持从文本、截图、Markdown 和 PDF 整理高质量学习卡片，并通过 AnkiConnect 导入本地 Anki。

An Anki card-making skill for turning text, screenshots, Markdown, and PDFs into structured study cards and syncing them to a local Anki installation through AnkiConnect.

## Features / 功能

- 词义题 / Vocabulary meaning questions
- 填空题 / Cloze cards
- 单选题 / Single-choice questions
- 多选题 / Multiple-choice questions
- 判断题 / True-false questions
- 简答题 / Short-answer questions
- 英语词汇卡：词性、音标、等级、词典释义、音频
- English vocabulary support: part of speech, phonetics, levels, dictionary definitions, and pronunciation audio
- 双语例句、词汇关系、其他含义、口诀和解读
- Bilingual examples, vocabulary relations, additional meanings, mnemonics, and explanations
- 浅色 / 深色模式，兼容桌面端和 Anki Mobile
- Light and dark themes for desktop and Anki Mobile
- 导入前校验与独立 HTML 预览
- Validation and standalone HTML preview before syncing
- 自定义 Anki 牌组
- Custom Anki deck selection

## Natural-Language Type Routing / 自然语言调用

可以直接描述想要的题型：

You can request a card type in natural language:

| 中文请求 | English request | `question_type` |
| --- | --- | --- |
| 整理成词义题 / 单词题 | Make vocabulary meaning cards | `vocabulary_meaning` |
| 整理成填空题 | Make cloze cards | `cloze` |
| 整理成单选题 | Make single-choice cards | `single_choice` |
| 整理成多选题 | Make multiple-choice cards | `multiple_choice` |
| 整理成判断题 / 判断正误 | Make true-false cards | `true_false` |
| 整理成简答题 | Make short-answer cards | `short_answer` |

Example / 示例：

```json
{
  "type": "Choice",
  "question_type": "true_false",
  "front": "线粒体是光合作用的主要场所。",
  "options": ["正确", "错误"],
  "correct_answer": "B",
  "explanation_zh": "光合作用主要发生在叶绿体中。"
}
```

## Card Data / 卡片数据

Cards are provided as a JSON array. The legacy `type` field identifies the Anki note model, while `question_type` identifies the learning interaction.

卡片使用 JSON 数组。旧版 `type` 表示 Anki 笔记模型，`question_type` 表示学习题型。

```json
[
  {
    "type": "Cloze",
    "question_type": "cloze",
    "front": "The manager remained {{c1::resilient}} after repeated setbacks.",
    "back": "",
    "tags": ["vocabulary", "ielts"]
  }
]
```

## Custom Decks / 自定义牌组

Command-line override / 命令行指定：

```bash
python3 scripts/anki_sync.py \
  --file cards.json \
  --deck "English Vocabulary"
```

Or configure the deck in a bundle / 也可以在 JSON 顶层配置：

```json
{
  "deck": "English Vocabulary",
  "cards": []
}
```

`--deck` takes precedence. If neither is provided, the default deck is `AnkiCardmaker`.

命令行 `--deck` 优先级最高；都没有时默认使用 `AnkiCardmaker`。

## Validate, Preview, Sync / 校验、预览、导入

```bash
python3 scripts/validate_cards.py --file cards.json
python3 scripts/preview_cards.py --file cards.json --output preview.html
python3 scripts/anki_sync.py --file cards.json --deck "My Deck"
```

Before syncing, open Anki and make sure AnkiConnect is running on `127.0.0.1:8765`.

导入前请打开 Anki，并确保 AnkiConnect 运行在 `127.0.0.1:8765`。

Cloze cards use the standard `Back Extra` field by default. Override it with `--cloze-extra-field` for a custom note type.

Cloze 卡片默认使用标准 `Back Extra` 字段；如果使用自定义笔记类型，可通过 `--cloze-extra-field` 覆盖。

## Repository Layout / 目录结构

- `SKILL.md`: detailed instructions for the Codex skill / Skill 详细规则
- `scripts/`: validation, preview, and Anki sync tools / 校验、预览、导入脚本
- `schemas/`: JSON schema / JSON Schema
- `examples/`: practice and test card payloads / 示例与测试卡片

## License

See the repository license file if provided.
