# Single-Choice Sub-skill / 单选题子模块

Use when exactly one option is correct.

- Use `type: Choice` and `question_type: single_choice`.
- Provide at least two non-empty options and one valid `correct_answer`.
- Render options with stable `A.`, `B.`, `C.` labels.
- Render each option as a button. The first click locks the card, marks the selected answer red when wrong and the correct answer green, then reveals the back.
- Keep the complete question and all options visible on the back with the answer and rationale.
- Do not add keyboard handlers; Anki keeps Space for flipping and `1`–`4` for grading.
- Apply the shared two-stage preview and explicit-import gate.
