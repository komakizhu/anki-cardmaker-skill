---
name: anki-cardmaker
description: Use when the user mentions 制卡、做卡、闪卡、卡片、Anki、anki、导入 Anki, or asks to turn screenshots, files, text, or notes into study cards. Route the request to the appropriate card-type sub-skill and require preview approval before importing.
---

# Anki Intelligent Card Maker

## Overview
Generate high-yield, memory-optimized Anki cards (Cloze, Choice, and QA) from any study material, automatically attach context-aware mnemonic hooks (humorous, analogies, visual prompts), and sync them directly to a local Anki deck via AnkiConnect.

## When to Use
- **Exam Preparation**: Studying for dense exams like Postgraduate Entrance Exam (考研), National Judiciary Exam (法考), Medical Licensure (执业医), or Civil Service Exams (考公/考编).
- **Language Acquisition**: Importing lists of raw vocabulary words and generating vocabulary meaning cards with collocations and sentence contexts; use Cloze only when explicitly requested or clearly present in the source.
- **Markdown & PDF Study Notes**: Directly parsing Markdown files or PDF study materials (converting PDF sections to Markdown first) to generate memory-optimized cards.

## Trigger and Card-Type Intake

Invoke this Skill when the user expresses card-making or Anki intent, including `制卡`、`做卡`、`闪卡`、`卡片`、`anki`、`Anki`、`导入 Anki`、`同步到 Anki`、`整理成卡片` or equivalent English phrases such as “make cards”, “flashcards”, or “import to Anki”. Do not require the user to say “Anki Skill”.

If the user has not specified a card type, ask before generating cards:

> 你想做成哪一种卡？
> 1. 词义题 / 单词题
> 2. 填空题 / Cloze
> 3. 单选题
> 4. 多选题
> 5. 判断题
> 6. 简答题

If the input is an isolated English word list, recommend `词义题 / 单词题` and explain that this is the default. If the user explicitly names a type, do not ask the same question again. Load the matching profile from `subskills/` and apply it as the card-specific contract.

### Card-Type Sub-skills

The sub-skills are local routing profiles, not separate import permissions. They define the front/back fields, required evidence, and generation rules for each interaction:

- `subskills/vocabulary-meaning/SKILL.md`: word meaning, dictionary, examples, relations, and polysemy
- `subskills/cloze/SKILL.md`: contextual blanks and real cloze passages
- `subskills/single-choice/SKILL.md`: one correct option
- `subskills/multiple-choice/SKILL.md`: multiple correct options
- `subskills/true-false/SKILL.md`: binary judgment cards
- `subskills/short-answer/SKILL.md`: concise question-and-answer cards

All sub-skills inherit the shared validation, preview gate, deck selection, theme, audio, and AnkiConnect rules in this file.

## Learning Stage Intake

Before generating English vocabulary cards, ask for the target learning stage unless it is already clear from the request or source metadata. Do not silently mix example difficulty across exams.

| Stage | Vocabulary difficulty | Sentence length / grammar | Context and exam scenes | Collocations |
| --- | --- | --- | --- | --- |
| `CET-4` | Common B1-B2 vocabulary | 8-18 words; basic clauses and common conjunctions | Campus, daily life, travel, workplace | CET-4 high-frequency fixed phrases |
| `CET-6` | B2-C1 abstract and academic vocabulary | 14-26 words; subordinate clauses and nominalization | Social issues, science, workplace, academic discussion | CET-6 academic and argumentative collocations |
| `中考英语` | A2-B1 core vocabulary | 6-15 words; basic tenses and short clauses | School, family, hobbies, health, daily life | Junior-high textbook phrases |
| `高考英语` | B1-B2 academic and social vocabulary | 12-24 words; compound and complex sentences | Campus, society, science, environment, culture | Gaokao reading and writing collocations |
| `TEM-4` | B2-C1 general and formal vocabulary | 14-26 words; formal clauses and discourse markers | University life, society, culture, workplace | TEM-4 reading and writing phrases |
| `TEM-8` | C1 advanced academic and literary vocabulary | 18-32 words; dense formal prose and embedded clauses | Academic, cultural, political, and literary topics | TEM-8 formal and academic collocations |
| `IELTS` | High-frequency general and academic vocabulary | 12-25 words; natural complex sentences | IELTS Reading, Writing, Speaking, and everyday situations | IELTS topic collocations and natural word partnerships |
| `TOEFL` | C1 university-level academic vocabulary | 18-32 words; dense explanatory and causal structures | University lectures, science, environment, psychology, social science | TOEFL lecture and academic-reading collocations |
| `GRE` | C1-C2 advanced, abstract, and low-frequency vocabulary | 20-38 words; dense argumentation and nuanced contrast | Humanities, science, history, philosophy, social theory | GRE high-level synonyms and academic collocations |
| `GMAT` | B2-C1 business and analytical vocabulary | 16-30 words; logic, comparison, and evidence structures | Business, economics, management, data, policy | GMAT business and analytical collocations |
| `BEC` | B1-C1 business and workplace vocabulary | 12-25 words; practical formal correspondence | Meetings, negotiation, sales, finance, human resources | Business collocations and email formulas |
| `学术英语` | C1 academic vocabulary and nominalization | 18-35 words; cautious claims, cause-effect, and evidence | Research, methodology, citations, lectures, papers | Academic verbs, noun phrases, and reporting patterns |
| `职场英语` | B1-C1 practical workplace vocabulary | 10-24 words; clear professional requests and updates | Meetings, projects, email, customer service, management | Workplace collocations and professional formulas |
| `考研英语一` | Academic vocabulary, rare meanings, abstract concepts | 18-35 words; long argumentative sentences and logical relations | Academic and social commentary, research, public policy | 考研英语一阅读高频搭配和熟词僻义语境 |
| `考研英语二` | Practical B2-C1 vocabulary | 14-28 words; moderately complex clauses | Workplace, economics, technology, society | 考研英语二实用主题和职场高频搭配 |
| `通用` | Balanced B1-C1 vocabulary | 10-25 words; moderate complexity | Mixed real-life and academic contexts | General high-frequency collocations |

Store the selected stage as `learning_stage` in the card bundle and on each vocabulary card when possible. If no stage is supplied, ask before Stage 1 generation:

> 你的目标学习阶段是什么：中考、高考、CET-4、CET-6、TEM-4、TEM-8、雅思、托福、GRE、GMAT、BEC、学术英语、职场英语、考研英语一、考研英语二，还是通用？

The selected stage must control five generation dimensions: vocabulary difficulty, sentence length, grammar complexity, context/exam scene, and high-frequency collocations. It changes example construction, not the core dictionary meaning. Keep the word's sense accurate and do not force an artificial exam context.

## Project Debug and Publish Workflow

During development, `.agents/skills/anki-cardmaker/` is the single source of truth. The repository root (`SKILL.md`, `scripts/`, `schemas/`, `examples/`, and `VERSION`) is the publish mirror only.

- Make Skill changes in `.agents/skills/anki-cardmaker/`.
- Before validation or publishing, run `python3 scripts/sync_project_skill.py` from the project root.
- Before committing, run `python3 scripts/sync_project_skill.py --check`; a non-zero result means the publish tree is stale.
- For vocabulary cards with `source_status: "verified"`, run `python3 scripts/verify_example_sources.py --file <cards.json>` after validation. This checks URL reachability and metadata shape only; it does not prove that a sentence came from the cited source.
- Do not hand-edit the root mirror after synchronization. If a root change is needed, apply it to the project source first and sync again.
- `.agents/` and Python cache files are local development artifacts and are excluded from the publish commit.

## Core Patterns

### 1. Minimal Information Principle (Atomization)
Never put too much text on a single card. Cut complex sentences into smaller, single-point questions.

```
❌ BAD QA (Overloaded):
Q: What is the pathogen of tuberculosis, its staining, and primary transmission route?
A: Mycobacterium tuberculosis, acid-fast positive staining, transmitted via airborne droplets/aerosols.

✅ GOOD QA (Atomized):
Card 1:
Q: What is the pathogen responsible for tuberculosis?
A: Mycobacterium tuberculosis

Card 2:
Q: What staining method is positive for Mycobacterium tuberculosis?
A: Acid-fast staining (酸性染色/抗酸染色)

Card 3:
Q: What is the primary transmission route of tuberculosis?
A: Airborne droplets / Aerosols (空气飞沫/气溶胶)
```

### 2. Contextual Cloze (挖空) for Language
Instead of translating vocabulary words in isolation, embed them in realistic sentences and use Cloze deletions.
- Bold the word.
- Identify common collocations.
- Put definitions, idioms, or usage notes in the Extra field.
- Use Cloze only when the user explicitly asks for blank-filling / cloze practice or the source contains a real passage with a meaningful blank.
- An isolated word list is not a Cloze source; it must use the vocabulary meaning workflow by default.

```markdown
Front:
Analyzing real exam readings, the researcher must {{c1::scrutinize::v. 仔细检查}} every sentence.

Extra:
- **Collocations**: scrutinize data / scrutinize details.
- **Synonyms**: examine closely, inspect.
- **Mnemonic**: "scrutinize" sounds like "screw tiny eyes" (眯起眼睛仔细看).
```

### 3. Objective Multiple Choice
Format multiple-choice questions cleanly. The front should present the question and choices, and the back should present the correct key along with an explanation.
- Option prefix: `A.`, `B.`, `C.`, `D.`
- Clean HTML output for Anki compatibility.

### 4. Mnemonic Hook Generation
AI must automatically attach a "memory hook" on the back of each card:
- A vivid analogy.
- A humorous joke, homophone (谐音梗), or story.
- If highly abstract, write a prompt to invoke an image generation tool (such as `generate_image`, DALL-E, or Midjourney) and link the local path under `mnemonic_image_path`.

### 5. Markdown (MD) Notes Parser
When generating cards from Markdown documents:
- Use heading hierarchies (`#`, `##`, `###`) to determine the card's context/category (reflected in tags or subheaders).
- Turn key lists, bullet points, and definitions into QA cards.
- Convert bold words (`**keyword**`) or highlighted terms into Cloze cards.

### 6. PDF (Converted to MD) Processing
When studying PDF textbooks or slides:
- Extract text content from target PDF pages or chapters.
- Format the extracted text into clean, structured Markdown format (restoring headers, lists, code snippets).
- Apply the Markdown atomization rules to split dense paragraphs into independent, focused cards.

### 7. Vocabulary Importing & Context Generation
When importing raw vocabulary lists (without examples or translations):
- For each word, generate a natural, exam-standard sentence (e.g., TOEFL/IELTS/SAT/CET-6 difficulty) showing the word in context.
- Create one `vocabulary_meaning` card per word by default. The front should show the generated sentence with the target word emphasized, and the back should lead with the word, part of speech, Chinese meaning, level, phonetic, and audio.
- Do not turn the generated sentence into a Cloze automatically. Only switch to `cloze` when the user explicitly requests it or the original material is a passage/exercise with a meaningful blank.
- Under the vocabulary support area, list the configured dictionary definitions, bilingual examples, vocabulary relations, other meanings, and mnemonic support.
- Match every generated example sentence to the confirmed `learning_stage`; do not reuse a generic example set across stages when stage-specific context would improve recall.
- Before rendering, check every example against the selected stage's five dimensions: difficulty, length, grammar, context, and collocations. If the card has three bilingual examples, vary the scenes while keeping all three within the same stage band.
- Prefer examples in this order: verified past-exam sentence, official exam sample or authoritative source text, then a stage-matched generated sentence. Never label a generated sentence as a past-exam question.
- For each authentic example, record its source in `example_sources` at the same index as `example_sentences`, including exam, year, section or question number, and a stable URL/page when available. If no source can be verified, use `自拟·阶段匹配例句` instead of inventing an attribution.

#### Vocabulary Meaning Card Contract

`type: "QA"` is only the Anki note model. It does not mean that the card is a generic question-and-answer card. Every English word card must use the pair:

```json
{
  "type": "QA",
  "question_type": "vocabulary_meaning"
}
```

For every isolated word-list item, the back must contain all of these modules whenever the information can be generated reliably:

1. Dictionary meaning: the word, part of speech, Chinese meaning, level, phonetic, audio, and Oxford/Collins-aligned definitions with Chinese notes.
2. Vocabulary relations: one clearly labeled block containing synonyms/antonyms, near-synonyms, confusable words, collocations, and word roots/affixes. Each lexical item must include a basic part of speech and Chinese gloss.
3. Bilingual examples: at least three English examples from different contexts, each followed by its aligned Chinese translation. The target word and its Chinese equivalent must be emphasized in the rendered card.
4. Other meanings: every additional sense must have one aligned example sentence, with the target word emphasized.

Do not downgrade a word card to generic `short_answer` merely because its Anki model is `QA`. Do not omit these modules just because the source was a screenshot or OCR result.

### 8. External App Export Upgrader (扇贝/百词斩/CSV)
When processing exported word files or CSV/TXT tables from other flashcard applications (like Shanbay, Baicizhan, or Quizlet):
- Map isolated word fields (e.g., word, phonetic, definition) to the vocabulary meaning template; map an included passage or explicit blank exercise to Cloze only when the source supports it.
- **Perform Quality Upgrades**: If the original app provides mechanical dictionary definitions or unnatural translations, replace them with concise, natural translations.
- **Generate Memory Aids**: Automatically attach high-frequency collocation structures and a mnemonic hook (jokes, homophones, analogies) to the back of the card, which are usually missing in standard app exports.

### 9. Polysemy (一词多义) & Rare Meanings (熟词僻义) Strategy
To avoid generating cards with incorrect definitions when processing polysemous words:
- **Prioritize Context**: If the input includes a context sentence, paragraph, or book chapter, the agent **MUST** bind the word's meaning to that specific context.
- **Avoid Ambiguous Fusion**: Never merge different parts of speech or distinct meanings into a single card front.
- **Split into Separate Cards**: If a raw word is imported without context and has multiple high-frequency meanings (e.g., *fine* as "excellent" vs. "monetary penalty"; *subject* as "topic" vs. "vulnerable to"), generate **separate cards** for each major meaning. Clearly distinguish the part of speech and definition on the front/back.
- **Target Rare Meanings (熟词僻义)**: For exam-prep targets (like 考研/IELTS), prioritize generating cards for the "rare meaning of common words" (e.g., *harbor* as a verb "to hold a thought/feeling"; *court* as a verb "to seek favor or invite danger"). Mark these cards clearly with a `[熟词僻义]` tag.

### 10. Processing Priority
Use the first rule that applies. Do not mix lower-priority behavior into a card if a higher-priority rule already decides it.

| Priority | Input situation | Required action |
| --- | --- | --- |
| 1 | Explicit user request for a type | Apply it to the batch; “单词题/词义题” always means `vocabulary_meaning` |
| 2 | Screenshot, OCR result, spreadsheet, or text containing one English word/phrase per row with no sentence or blank | Create one `vocabulary_meaning` card per item. This hard rule overrides the fact that the input is an image |
| 3 | Real passage/exercise with visible blanks, answer slots, `{{c1::...}}`, or an explicit Cloze request | Use `cloze` and preserve the source context |
| 4 | Definition prompt such as “What is the definition/meaning of 'word' ...?” | Convert to `vocabulary_meaning`, never generic `问答题` |
| 5 | Multiple meanings or polysemous word without enough context | Split into separate cards |
| 6 | Dense factual paragraph | Atomize into one fact per card |
| 7 | Abstract or difficult concept | Add a mnemonic hook |
| 8 | Highly visual or especially abstract content | Optionally attach `mnemonic_image_path` |
| 9 | Exported CSV / third-party flashcard data | Normalize field names and upgrade mechanical wording |

### 11. Output Rules
- Prefer JSON arrays of card objects.
- Include `schema_version` when available.
- Keep `source` metadata when the input came from a file, page, chapter, URL, or screenshot.
- Never emit cards with empty required fields.
- Validate before previewing or syncing.
- For English-learning cards, keep the configured bilingual layout and provide both English and Chinese support where the card type requires it.
- For non-English professional or subject-matter cards, keep the question, answer, explanation, and mnemonic in Chinese whenever possible. Do not translate the explanation or mnemonic into English merely to fill a field; preserve unavoidable technical names, formulas, abbreviations, and original quotations only when they are needed for accuracy.
- For Chinese subject cards, prefer `back_zh`, `explanation_zh`, and `mnemonic_hook_zh` as the rendered Chinese content fields. Do not add an English parallel line unless the user explicitly requests bilingual output.
- Keep Chinese explanations concise and literal enough to support recall, not a long essay.

### Card Type Catalog

Use `question_type` to make the intended learning interaction explicit. The legacy `type` field remains the Anki note model and is still supported.

| `question_type` | Chinese label | Anki `type` | Use for |
| --- | --- | --- | --- |
| `vocabulary_meaning` | 词义题 | `QA` | Meaning of a target word in a sentence or phrase |
| `cloze` | 填空题 | `Cloze` | Recall a missing word, phrase, or fact in context |
| `single_choice` | 单选题 | `Choice` | Exactly one correct option |
| `multiple_choice` | 多选题 | `Choice` | More than one correct option |
| `true_false` | 判断题 | `Choice` | Decide whether one statement is true or false |
| `short_answer` | 简答题 | `QA` | Chinese or English free-response recall |

Accepted aliases include `词义题`, `填空题`, `单选题`, `多选题`, `判断题`, `简答题`, `单词题`, `meaning`, `definition`, `fill_blank`, `single-choice`, `multiple-choice`, and `true-false`. If `question_type` is omitted, it is inferred from the legacy `type` and card content.

### Natural-Language Type Routing

When the user asks to organize or convert material, infer the requested `question_type` from their wording and apply it to the whole batch unless they specify exceptions:

| User wording | Use |
| --- | --- |
| “整理成词义题”, “做成单词题”, “按词义考”, “考这个词在句中的意思” | `vocabulary_meaning` |
| “整理成填空题”, “挖空”, “做 Cloze” | `cloze` |
| “整理成单选题”, “只有一个正确答案” | `single_choice` |
| “整理成多选题”, “有多个正确答案” | `multiple_choice` |
| “整理成判断题”, “判断正误”, “对错题” | `true_false` |
| “整理成简答题”, “问答题”, “让用户自己回答” | `short_answer` |

“单词题” means `vocabulary_meaning` when the target is a word used in a sentence; it does not mean a bare translation list. A vocabulary meaning card must preserve the sentence context and include the configured dictionary fields.

### Input-Shape Priority

When the requested type is not explicit, classify the source before generating cards. Use the first matching rule below:

1. **Explicit user request wins**: “词义题”, “单词题”, “单词释义”, “解释这些词”, or “一个个词回答” selects `vocabulary_meaning`. “填空题”, “完形填空”, “Cloze”, or “挖空” selects `cloze` only when explicitly requested.
2. **Isolated word-list hard gate**: if each visual/text row is a standalone English word or short lexical phrase with no sentence, blank, answer slot, or passage context, route the entire batch to `vocabulary_meaning`.
3. **Real blank structure selects Cloze**: a passage or exercise contains visible blanks, answer slots, `{{c1::...}}`, or an obvious missing word/phrase task. A generated example sentence is not a blank structure.
4. **Definition prompts select vocabulary meaning**: “What is the definition/meaning of 'word' ...?” is `vocabulary_meaning`, even if the legacy Anki type is `QA`.
5. **Mixed input is split by shape**: keep genuine passage blanks as Cloze and convert isolated words to vocabulary meaning cards.

Never infer Cloze merely because a generated example sentence, screenshot, or `word` field is available. A generated sentence supplies context for a vocabulary meaning card; it is not evidence that the user requested a blank-filling exercise.

### Routing Guardrails

- Every isolated English word from a vocabulary screenshot must carry `question_type: "vocabulary_meaning"` and `type: "QA"`.
- Populate `word`, `part_of_speech`, `definition_zh`, `word_level`, `phonetic`, and the configured dictionary fields. Do not wrap the generated example sentence in `{{c1::...}}`.
- A vocabulary card is incomplete if its rendered back has no vocabulary relations, no bilingual example section, or no other-meanings section. If a field cannot be verified, state that it needs review rather than silently dropping the module.
- Use `question_type: "cloze"` only when `input_shape` is `passage_blank` or `explicit_cloze_request` is `true`.
- `question_type: "short_answer"` is reserved for conceptual free-response questions, not single English words or English definition prompts.
- If OCR is uncertain but the visual layout is clearly a word list, choose `vocabulary_meaning`; do not fall back to Cloze or QA.

For `true_false`, generate exactly two options, normally `正确` and `错误`, and set `correct_answer` to `A` or `B`:

```json
{
  "type": "Choice",
  "question_type": "true_false",
  "front": "线粒体是细胞进行光合作用的主要场所。",
  "options": ["正确", "错误"],
  "correct_answer": "B",
  "explanation": "Photosynthesis mainly occurs in chloroplasts, not mitochondria.",
  "explanation_zh": "光合作用主要发生在叶绿体中，而不是线粒体中。"
}
```

### 12. Automatic UI Logic
- Show the front as the only question space.
- Show the back as the only support space: answer, explanation, and mnemonic.
- Keep the back visually minimal with no decorative badges, source breadcrumbs, or helper panels.
- Render Chinese follow-up lines as plain text without a `中文：` prefix.
- For cloze cards, keep the card content focused on the cloze and the answer; do not add extra visual chrome.

### Formula Rendering

- Preserve LaTeX formulas instead of flattening them into plain text.
- Use `\(...\)` for inline formulas and `\[...\]` for display formulas. `$...$` and `$$...$$` are also supported.
- The standalone HTML preview and generated Anki card sides load the same MathJax configuration.
- Do not escape, translate, or rewrite backslashes inside formulas during card generation.
- If the user needs fully offline review, package a local MathJax asset instead of relying on the CDN; otherwise the default CDN-backed renderer is used.

### Mandatory Two-Stage Import Gate

Every card-making operation must stop after Stage 1 until the user explicitly approves the import.

1. **Build and show**: generate the cards, validate them, render an HTML preview or equivalent front/back sample, and propose a deck name. If the user did not provide a deck name, suggest one based on the subject and ask for approval.
2. **Import after approval**: only after an explicit confirmation such as “同意导入”, “确认”, “导入这个牌组” or “sync it” may the skill call AnkiConnect or run the sync command. Use the approved deck name and report the import result.

Never silently import immediately after generating cards. “生成”, “整理”, “做成卡片” or “给我看看” means Stage 1 only; it is not permission to write to Anki.

----

## JSON Card Schema

Generate cards in the following JSON format:

```json
[
  {
    "type": "QA",
    "front": "What staining method is positive for Mycobacterium tuberculosis?",
    "back": "Acid-fast staining (抗酸染色)",
    "explanation": "Mycobacterium tuberculosis has lipid-rich cell walls that resist decolorization by acid-alcohol, remaining red.",
    "mnemonic_hook": "Acid-fast -> 'Acid' eats color but tuberculosis holds 'fast' (stays red).",
    "mnemonic_image_path": "/absolute/path/to/generated_image.png",
    "tags": ["medical", "microbiology"]
  },
  {
    "type": "Cloze",
    "front": "Analyzing real exam readings, the researcher must {{c1::scrutinize::仔细检查}} every sentence.",
    "back": "",
    "explanation": "scrutinize means to examine or inspect closely and thoroughly.",
    "mnemonic_hook": "Scrutinize: 'screw tiny eyes' (眯起眼睛仔细看)",
    "tags": ["ielts", "vocabulary"]
  },
  {
    "type": "Choice",
    "front": "下列关于宪法修正案的说法，正确的是哪一项？",
    "options": [
      "修正案须由全国人大主席团公布",
      "修正案须由全国人大代表三分之二以上多数通过",
      "修正案草案的提议权属于五分之一以上的全国人大代表",
      "修正案草案须经全国人大常委会全体委员过半数通过"
    ],
    "correct_answer": "C",
    "explanation": "我国宪法修改由全国人大常委会或者五分之一以上的全国人大代表提议，并由全国人民代表大会以全体代表的三分之二以上的多数通过。公布权属于全国人大主席团，但通过门槛是全体代表的三分之二，C选项提议权符合宪法第64条规定。",
    "mnemonic_hook": "宪法修改『五提三通』：5个人提意见（1/5代表），3个人举手通过（2/3多数）。",
    "tags": ["法考", "宪法"]
  }
]
```

---

## Execution Workflow

1. **Intake & Conversion**:
   - Accept user inputs: raw text, screenshots, Markdown notes (`.md`), or PDF files (`.pdf`).
   - If input is a PDF, use text extraction commands or read contents, then format key chapters as structured Markdown.
   - If input is a raw vocabulary list, proceed to Context Generation.
2. **Extraction & Atomization**:
   - Parse Markdown structures, headings, and lists.
   - For vocabulary terms, auto-generate contextual sentences.
   - Split complex materials into independent QA, Cloze, or Choice templates using the Minimal Information Principle.
3. **Mnemonic Design**:
   - For difficult concepts or raw words, generate mnemonic hooks.
   - Optional: Use an image generation tool to create visual cards for highly abstract terms and save the graphic to a local directory, setting the path in `mnemonic_image_path`.
4. **Export JSON**: Output the final cards list as a JSON array to a temporary `cards.json` file.
5. **Validate First**: Run the validator before showing the preview:
   ```bash
   python3 scripts/validate_cards.py --file cards.json
   ```
6. **Stage 1 Preview and Deck Proposal**: Render a standalone HTML preview, show the result, and propose the target deck. Do not sync yet:
   ```bash
   python3 scripts/preview_cards.py --file cards.json --output preview.html
   ```
7. **Stage 2 Sync After Explicit Approval**: Only after the user confirms the preview and deck, run the import command:
   ```bash
   python3 scripts/anki_sync.py --file cards.json --deck "MyDeckName"
   ```
   *Note: Ensure the local Anki app is open and running with AnkiConnect active. Cloze notes use the standard `Back Extra` field by default, but the field name can be overridden with `--cloze-extra-field` if the user uses a custom Cloze note type.*

To choose a deck, pass `--deck "My Deck"`. A JSON bundle can also set the deck once for the whole import:

```json
{
  "deck": "English Vocabulary",
  "cards": [
    {"question_type": "cloze", "type": "Cloze", "front": "The {{c1::resilient}} team recovered quickly."}
  ]
}
```

The command-line `--deck` value takes precedence over the bundle's `deck`; if neither is provided, the default is `AnkiCardmaker`.

## Validation Assets

- `schemas/anki_card.schema.json`: formal schema for QA, Cloze, and Choice cards.
- `examples/cards.sample.json`: minimal sample payload for smoke testing.
- `scripts/validate_cards.py`: preflight validation without touching Anki.
- `scripts/test_regression.py`: dependency-free regression suite for routing, validation, stage propagation, source alignment, audio HTML, and mobile HTML/CSS contracts.
- `scripts/verify_example_sources.py`: URL reachability check for verified vocabulary-example sources.
- `scripts/preview_cards.py`: static HTML preview generator for front/back inspection.
- `scripts/card_validation.py`: shared validation and normalization logic used by every entry point.

The shared validator enforces the mechanical rules before preview or sync: supported card type and required answer fields, Chinese QA `back_zh`, valid Cloze deletions, Choice answer bounds, vocabulary dictionary fields, Oxford/Collins translation pairs, aligned bilingual example arrays, one-to-one other-meaning examples, and part-of-speech plus Chinese glosses for vocabulary relation entries. For isolated vocabulary imports it additionally requires the learning stage, source status, three aligned bilingual examples and stage-carrying generated source labels, dictionary definition pairs, the complete vocabulary-relations block, and other-meaning examples. `source_status: "needs_review"` blocks preview and sync. It does not attempt to judge whether examples are genuinely from different contexts or whether a dictionary definition is semantically accurate; those remain generation and review responsibilities.

Run the regression suite after changing routing, validation, audio, or card CSS:

```bash
python3 scripts/test_regression.py
```

The suite intentionally uses only the Python standard library. Its HTML snapshots are stable structural contracts rather than pixel screenshots, so they work in CI and still catch missing one-click audio controls or mobile layout rules.

## Card Fields

- `question_type`: explicit learning interaction; use `vocabulary_meaning`, `cloze`, `single_choice`, `multiple_choice`, `true_false`, or `short_answer`.
- `type`: Anki note model. Use `QA` for vocabulary meaning and short-answer cards, but always use `question_type` to distinguish them.
- `learning_stage`: target English learning stage, such as `中考英语`, `高考英语`, `CET-4`, `CET-6`, `TEM-4`, `TEM-8`, `IELTS`, `TOEFL`, `GRE`, `GMAT`, `BEC`, `学术英语`, `职场英语`, `考研英语一`, `考研英语二`, or `通用`.
- `input_shape`: optional routing evidence; use `isolated_vocabulary_list`, `passage_blank`, `explicit_cloze_request`, `definition_prompt`, or `concept_question`.
- `explicit_cloze_request`: optional boolean. Required when `question_type` is `cloze` without `input_shape: "passage_blank"`.
- `front`: question or cloze text shown on the front.
- `back`: answer text for QA cards.
- `explanation`: English explanation or rationale.
- `explanation_zh`: Chinese follow-up line for the explanation, shown as plain text with no `中文：` prefix.
- `back_zh`: Chinese follow-up line for the answer text, shown as plain text with no `中文：` prefix.
- `mnemonic_hook`: memory cue.
- `mnemonic_hook_zh`: Chinese follow-up line for the mnemonic cue, shown as plain text with no `中文：` prefix.
- `part_of_speech`: optional part of speech, such as `v.` or `adj.`.
- `phonetic`: optional phonetic transcription.
- `definition_zh`: concise Chinese dictionary meaning for a vocabulary card.
- `word_level`: optional learning level, such as `CET-4`, `CET-6`, or `IELTS`.
- `oxford_definition`: optional Oxford-aligned English definition; provide only when sourced or verified.
- `collins_definition`: optional Collins-aligned English definition; provide only when sourced or verified.
- `oxford_definition_zh`: Chinese note corresponding to the Oxford sense.
- `collins_definition_zh`: Chinese note corresponding to the Collins sense.
- `explanation_target_zh`: Chinese target word or phrase to emphasize inside `explanation_zh`.
- `mnemonic_target_zh`: Chinese target word or phrase to emphasize inside `mnemonic_hook_zh`.
- `near_synonyms`: optional near-synonym list; each item should include a basic meaning.
- `confusable_words`: optional visually similar or easily confused words; each item should include a basic meaning.
- `collocations`: optional fixed collocation list with a concise Chinese meaning where useful.
- `word_root`: optional word root explanation.
- `word_affixes`: optional prefix/suffix explanation.
- `example_sentences`: at least three English examples in different contexts when supplied.
- `example_sentences_zh`: Chinese translations aligned with `example_sentences`.
- `example_targets_zh`: the Chinese target word/phrase for each bilingual example, aligned with `example_sentences_zh` and bolded in the rendered card.
- `example_sources`: source labels aligned one-to-one with `example_sentences`; identify verified real examples, or explicitly label generated examples as `自拟·阶段匹配例句`. Required for isolated vocabulary imports.
- `source_status`: provenance state for vocabulary examples: `verified` means the source metadata passed format checks and any supplied URL passed reachability checks; `generated` means every source label begins with `自拟·`; `needs_review` blocks preview and sync. The validator never treats this field as proof of semantic authenticity.
- `other_meanings`: other common senses of the target word.
- `other_meanings_examples`: one example sentence for each item in `other_meanings`; the target word is emphasized in the rendered sentence.
- `core_keywords`: automatically extracted or manually supplied core keywords.
- `synonyms`: optional synonym hints; each item should include a basic part-of-speech and Chinese meaning, such as `interesting adj. 有趣的`.
- `antonyms`: optional antonym hints; each item should include a basic part-of-speech and Chinese meaning.
- `contrast_terms`: optional contrast cues surfaced from the card.
- `example_sentence`: optional or automatically generated example sentence.
- `example_sentence_zh`: Chinese translation of the example sentence.
- `mnemonic_image_path`: optional local image path for visual memory aid.
- `source`: optional metadata for title, chapter, file, url, and page.
- `tags`: topic tags shown as chips in the card footer.

For a single-word vocabulary card, fill `part_of_speech`, `phonetic`, `definition_zh`, and `word_level`. Isolated vocabulary imports must also include `learning_stage`, `source_status`, three aligned bilingual examples and sources, Oxford/Collins definitions with Chinese notes, every vocabulary-relations field, and at least one other meaning with an aligned example. When reliable dictionary sources are available, fill `oxford_definition` and `collins_definition` with concise, sense-specific wording. Do not invent dictionary attributions; use `source_status: "generated"` for self-written examples and `needs_review` until uncertain provenance is resolved.

A QA prompt matching `What is the definition of 'word' in the phrase/sentence '...' ?` or `What is the rare meaning of 'word' in the sentence '...' ?` is a vocabulary meaning question. Render it as `词义题` with the example sentence on the front, not as a generic `问答题`.
