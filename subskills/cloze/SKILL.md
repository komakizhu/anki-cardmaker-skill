# Cloze Sub-skill / 填空题子模块

Use for explicit Cloze requests or source material containing meaningful blanks, such as passages and cloze exercises.

- Use `type: Cloze` and `question_type: cloze`.
- Preserve valid `{{c1::answer::hint}}` deletions.
- Do not convert an isolated word list into Cloze.
- Keep the answer and explanation focused on the deleted content.
- Use `Back Extra` by default for supplementary content.
- Apply the shared two-stage preview and explicit-import gate.
