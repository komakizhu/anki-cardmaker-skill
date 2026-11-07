---
name: anki-cardmaker-true-false
description: "用户要求“判断题、判断正误、对错题”或 “true-false、true-or-false、judgment”时调用。"
---

# Anki True-False Cards

- Generate `type: Choice` with `question_type: true_false`.
- Provide exactly two options representing true and false.
- Keep each front to one testable claim and explain the judgment on the back.
- Render both judgment options as buttons. The first click locks the card, shows red/green feedback, and reveals the back.
- Keep the claim and both options visible on the back with the answer and explanation.
- Do not add keyboard handlers; Anki retains Space for flipping and `1`–`4` for grading.
- Follow the shared implementation and two-stage import gate in `anki-cardmaker/SKILL.md`.
