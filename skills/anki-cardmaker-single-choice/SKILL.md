---
name: anki-cardmaker-single-choice
description: "用户要求“单选题”或 “single-choice、single-answer”时调用。"
---

# Anki Single-Choice Cards

- Generate `type: Choice` with `question_type: single_choice`.
- Provide at least two options and exactly one correct answer.
- Render each option as a button. The first click locks the card, marks a wrong selection red and the correct option green, then reveals the back.
- Keep the question and all options visible on the back with the correct answer and rationale.
- Do not add keyboard handlers; Anki retains Space for flipping and `1`–`4` for grading.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
