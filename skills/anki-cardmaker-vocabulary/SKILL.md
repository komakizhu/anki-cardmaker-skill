---
name: anki-cardmaker-vocabulary
description: Use when the user asks for vocabulary meaning cards, word cards, 单词题, 词义题, or an isolated English word list.
---

# Anki Vocabulary Meaning Cards

Use this callable profile for isolated English words and vocabulary screenshots.

- Generate `type: QA` with `question_type: vocabulary_meaning`.
- Ask for the English learning stage when it is not provided.
- Include dictionary meaning, part of speech, Chinese gloss, level, phonetic, audio, Oxford/Collins notes, three bilingual examples, vocabulary relations, and other meanings with examples.
- Never route an isolated word list to Cloze or generic short answer.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
