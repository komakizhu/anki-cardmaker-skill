---
name: Anki入口
description: 用户输入 `/anki`，或说“制卡、做卡、闪卡、导入 Anki、make cards、create flashcards、flashcards、import to Anki”时调用，显示中英双语题型菜单。
---

# Anki Cardmaker Launcher

When invoked as `/anki`, show this bilingual card-type menu before generating cards:

1. 制卡 / make cards
2. 做卡 / create flashcards
3. 闪卡 / flashcards
4. 导入 Anki / import to Anki
5. 词义题 / vocabulary meaning
6. 填空题 / cloze / fill-in-the-blank
7. 单选题 / single-choice
8. 多选题 / multiple-choice
9. 判断题 / true-or-false
10. 简答题 / short-answer

If the user selects a general card-making action without a type, ask which card type they want. Route a selected type to the matching `anki-cardmaker-*` Skill. Inherit the shared preview-first and explicit-import gate from `anki-cardmaker`.
