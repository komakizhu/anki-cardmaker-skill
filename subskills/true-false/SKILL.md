# True-False Sub-skill / 判断题子模块

Use for binary true/false judgments.

- Use `type: Choice` and `question_type: true_false`.
- Provide exactly two options representing true and false.
- Keep the front as one testable claim and explain the judgment on the back.
- Render both judgment options as buttons. The first click locks the card, shows red/green feedback, and reveals the back.
- Keep the claim and both options visible on the back with the answer and explanation.
- Do not add keyboard handlers; Anki keeps Space for flipping and `1`–`4` for grading.
- Apply the shared two-stage preview and explicit-import gate.
