# Multiple-Choice Sub-skill / 多选题子模块

Use when two or more options may be correct.

- Use `type: Choice` and `question_type: multiple_choice`.
- Provide at least two options and a `correct_answer` containing all correct option letters.
- Explain why the correct options are valid and the distractors are not.
- Let the learner select and clear options, then submit the full set. Submission locks the choices, shows red/green feedback, and reveals the back.
- Keep the complete question and all options visible on the back with the answer and explanation.
- Do not add keyboard handlers; Anki keeps Space for flipping and `1`–`4` for grading.
- Apply the shared two-stage preview and explicit-import gate.
