# Anki Intelligent Card Maker (anki-cardmaker)

An Antigravity custom skill designed to automatically extract, atomize, and generate high-yield study cards from multiple input formats and import them directly to local Anki without manual file exports.

## Core Features

- **Multi-source Processing**: Supports card creation from text inputs, OCR/screenshots, Markdown files, or PDF study materials.
- **Auto Context Generation**: Generates high-quality context sentences, translations, and common collocation lists for raw vocabulary words.
- **Sleek Formatting**: Output cards are cleanly structured in HTML with responsive styles for both Desktop and Mobile Anki readers.
- **Zero-Dependency Syncing**: Includes a Python script `anki_sync.py` that utilizes only standard library modules to interact with local Anki via AnkiConnect.

---

## Installation

To import this skill to your Antigravity setup:

1. Clone this repository into your global custom skills folder:
   ```bash
   git clone https://github.com/<your-username>/anki-cardmaker-skill.git ~/.gemini/config/skills/anki-cardmaker
   ```

2. Make sure the local python helper script is executable:
   ```bash
   chmod +x ~/.gemini/config/skills/anki-cardmaker/scripts/anki_sync.py
   ```

---

## Configuration & Requirements

1. Ensure the desktop **Anki** app is running.
2. Install the **AnkiConnect** add-on in Anki:
   - Go to `Tools` -> `Add-ons` -> `Get Add-ons`.
   - Input code: `2055492159` and restart Anki.

---

## How to Invoke the Agent

Simply ask your agent in Antigravity to make cards using `anki-cardmaker`. For example:
- *"Extract study cards from this textbook PDF/Markdown note"*
- *"Create choice questions from this political exam screenshot"*
- *"Import these words to Anki with contexts: scrutinize, ambiguity, anomaly"*
