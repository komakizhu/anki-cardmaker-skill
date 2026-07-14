---
name: 填空题
description: 用户要求“填空题、完形填空、挖空”或 “Cloze、cloze deletion、fill-in-the-blank、fill in the blanks”时调用。
---

# Anki Cloze Cards

Use this callable profile for explicit blanks and real passage-based cloze exercises.

- Generate `type: Cloze` with `question_type: cloze`.
- Preserve valid `{{c1::answer::hint}}` deletions.
- Do not convert an isolated English word list to Cloze.
- Use `Back Extra` by default for supplementary content.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
