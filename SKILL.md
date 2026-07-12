---
name: anki-cardmaker
description: Use when the user requests generating study or memory cards for Anki from screenshots, files, text inputs, or notes, and syncing them directly to Anki via AnkiConnect.
---

# Anki Intelligent Card Maker

## Overview
Generate high-yield, memory-optimized Anki cards (Cloze, Choice, and QA) from any study material, automatically attach context-aware mnemonic hooks (humorous, analogies, visual prompts), and sync them directly to a local Anki deck via AnkiConnect.

## When to Use
- **Exam Preparation**: Studying for dense exams like Postgraduate Entrance Exam (考研), National Judiciary Exam (法考), Medical Licensure (执业医), or Civil Service Exams (考公/考编).
- **Language Acquisition**: Importing lists of raw vocabulary words and auto-generating contextual cloze tests with collocations and sentence contexts.
- **Markdown & PDF Study Notes**: Directly parsing Markdown files or PDF study materials (converting PDF sections to Markdown first) to generate memory-optimized cards.

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
- Format the target word into a Cloze deletion, like `{{c1::vocabulary_word::Chinese_translation}}`.
- Under the Extra field, list at least two common collocations and a mnemonic hook.

### 8. External App Export Upgrader (扇贝/百词斩/CSV)
When processing exported word files or CSV/TXT tables from other flashcard applications (like Shanbay, Baicizhan, or Quizlet):
- Map fields (e.g., word, phonetic, definition, raw sentence) to the QA or Cloze template.
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
| 1 | Context sentence, paragraph, chapter, or screenshot with visible context | Preserve context and bind meaning to the provided source |
| 2 | Multiple meanings or polysemous word without enough context | Split into separate cards |
| 3 | Dense factual paragraph | Atomize into one fact per card |
| 4 | Vocabulary list without examples | Generate a contextual sentence before carding |
| 5 | Abstract or difficult concept | Add a mnemonic hook |
| 6 | Highly visual or especially abstract content | Optionally attach `mnemonic_image_path` |
| 7 | Exported CSV / third-party flashcard data | Normalize field names and upgrade mechanical wording |

### 11. Output Rules
- Prefer JSON arrays of card objects.
- Include `schema_version` when available.
- Keep `source` metadata when the input came from a file, page, chapter, URL, or screenshot.
- Never emit cards with empty required fields.
- Validate before previewing or syncing.
- When explaining a card, include both `explanation` in English and `explanation_zh` in Chinese.
- Keep `explanation_zh` concise and literal enough to support recall, not a long essay.
- For answer text and mnemonic hooks, use `back_zh` and `mnemonic_hook_zh` when a Chinese rendering is needed.

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
5. **Validate First**: Run the validator before import:
   ```bash
   python3 scripts/validate_cards.py --file cards.json
   ```
6. **Preview Before Sync**: Render a standalone HTML preview when you want to inspect front/back layout:
   ```bash
   python3 scripts/preview_cards.py --file cards.json --output preview.html
   ```
7. **Sync to Anki**: Run the python script to import:
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
- `scripts/preview_cards.py`: static HTML preview generator for front/back inspection.
- `scripts/card_validation.py`: shared validation and normalization logic used by every entry point.

The shared validator enforces the mechanical rules before preview or sync: supported card type and required answer fields, Chinese QA `back_zh`, valid Cloze deletions, Choice answer bounds, vocabulary dictionary fields, Oxford/Collins translation pairs, aligned bilingual example arrays, one-to-one other-meaning examples, and part-of-speech plus Chinese glosses for vocabulary relation entries. It does not attempt to judge whether examples are genuinely from different contexts or whether a dictionary definition is semantically accurate; those remain generation and review responsibilities.

## Card Fields

- `question_type`: explicit learning interaction; use `vocabulary_meaning`, `cloze`, `single_choice`, `multiple_choice`, `true_false`, or `short_answer`.
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

For a single-word vocabulary card, fill `part_of_speech`, `phonetic`, `definition_zh`, and `word_level`. When reliable dictionary sources are available, also fill `oxford_definition` and `collins_definition` with concise, sense-specific wording. Do not invent dictionary attributions.

A QA prompt matching `What is the definition of 'word' in the phrase/sentence '...' ?` or `What is the rare meaning of 'word' in the sentence '...' ?` is a vocabulary meaning question. Render it as `词义题` with the example sentence on the front, not as a generic `问答题`.
