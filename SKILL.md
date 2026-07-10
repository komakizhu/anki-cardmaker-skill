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
- Put definitions, idioms, or usage notes in the Back Extra field.

```markdown
Front:
Analyzing real exam readings, the researcher must {{c1::scrutinize::v. 仔细检查}} every sentence.

Back Extra:
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
- If highly abstract, write a prompt to invoke `generate_image` and link the local path under `mnemonic_image_path`.

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
- Under the Back Extra field, list at least two common collocations and a mnemonic hook.

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
   - Optional: Use the `generate_image` tool to create visual cards for highly abstract terms and save the graphic to `<appDataDir>/brain/<conversation-id>/scratch/mnemonic_X.png`.
4. **Export JSON**: Output the final cards list as a JSON array to a temporary `cards.json` file in the scratch directory.
5. **Sync to Anki**: Sync using the python script:
   ```bash
   python3 /Users/mac/.gemini/config/skills/anki-cardmaker/scripts/anki_sync.py --file /Users/mac/.gemini/antigravity/brain/<conversation-id>/scratch/cards.json --deck "MyDeckName"
   ```
   *Note: Ensure the local Anki app is open and running with AnkiConnect active.*
