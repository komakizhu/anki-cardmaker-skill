---
name: anki-cardmaker-multiple-choice
description: "用户要求“多选题”或 “multiple-choice、multiple-answer”时调用。"
---

# Anki Multiple-Choice Cards

- Generate `type: Choice` with `question_type: multiple_choice`.
- Provide at least two options and all correct option letters.
- Explain correct options and distractors on the back.
- Let the learner select and clear options before submitting the full set. Submission locks the options, shows red/green feedback, and reveals the back.
- Keep the question and all options visible on the back with the answer and explanation.
- Do not add keyboard handlers; Anki retains Space for flipping and `1`–`4` for grading.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
