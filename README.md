# AI-Agent Anki Intelligent Card Maker

A system instruction (prompt) and syncing engine designed for **any AI Agent** (such as Claude Code, Cursor, ChatGPT, or Antigravity) to automatically extract, atomize, and generate high-yield study cards from multiple input formats and import them directly to local Anki without manual file exports.

## Core Features

- **Multi-source Processing**: Auto-generates card sets from text, PDF, Markdown files, or screenshots/OCR images.
- **Context-Aware Cloze & QA**: Atomizes dense paragraphs into minimal information cards. Automatically designs context sentences and collocations for raw vocabulary words.
- **Mnemonic Hooks**: Employs creative analogies and mnemonic jokes, with support for image generation prompts.
- **External Wordlist Upgrader**: Seamlessly imports and upgrades raw flashcard/vocabulary exports (e.g., Shanbay, Baicizhan, or Quizlet CSVs) with contextual examples and memory aids.
- **Polysemy & Rare Meanings Protection**: Mitigates dictionary ambiguity by binding meanings to active contexts, splitting polysemous terms into distinct cards, and target-highlighting "rare meanings of common words" (熟词僻义) for exam syllabi.
- **Zero-Dependency Syncing**: Includes a Python script `anki_sync.py` that uses only standard Python libraries to interact with local Anki via AnkiConnect.

---

## How it Works & Installation

You can use this with any AI Agent in two steps:

### 1. Give the Instructions to your AI Agent
Provide the contents of [SKILL.md](SKILL.md) to your AI Agent as part of its system prompt, custom instructions, or reference files. This teaches the agent how to:
- Classify inputs into Cloze, Choice, and QA card schemas.
- Atomize text according to the Minimal Information Principle.
- Format card outputs as a JSON array.

### 2. Make the Sync Script Executable
Clone this repository locally and ensure the Python helper script is executable:
```bash
git clone https://github.com/komakizhu/anki-cardmaker-skill.git
chmod +x anki-cardmaker-skill/scripts/anki_sync.py
```

---

## Configuration & Requirements

1. Ensure the desktop **Anki** app is running.
2. Install the **AnkiConnect** add-on in Anki:
   - Go to `Tools` -> `Add-ons` -> `Get Add-ons`.
   - Input code: `2055492159` and restart Anki.

---

## How to Invoke the Agent

Simply ask your AI Agent to generate cards. For example:
- *"Extract study cards from this PDF/Markdown note"*
- *"Create choice questions from this political exam screenshot"*
- *"Import these words to Anki with contexts: scrutinize, ambiguity, anomaly"*

For terminal-based agents (e.g. Claude Code or Antigravity), they can automatically write the cards list to `cards.json` and execute the sync script in one step:
```bash
python3 scripts/anki_sync.py --file cards.json --deck "MyDeck"
```
