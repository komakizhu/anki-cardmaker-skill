---
name: anki-cardmaker-cloze
description: Use when the user asks for Cloze, cloze deletion, fill-in-the-blank, 完形填空, or 填空题 cards.
---

# Anki Cloze Cards

Use this callable profile for explicit blanks and real passage-based cloze exercises.

- Generate `type: Cloze` with `question_type: cloze`.
- Preserve valid `{{c1::answer::hint}}` deletions.
- Do not convert an isolated English word list to Cloze.
- Use `Back Extra` by default for supplementary content.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
