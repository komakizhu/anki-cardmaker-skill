---
name: 闪卡入口
description: 用户输入 `/闪卡`，或说“制卡、做卡、闪卡、导入 Anki、make cards、create flashcards、flashcards、import to Anki”时调用，显示中英双语题型菜单。
---

# 闪卡制作入口 / Flashcard Maker Launcher

当用户输入 `/闪卡` 时，先显示以下中英双语菜单，不直接猜题型或导入：

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

用户选择题型后，路由到对应的 `anki-cardmaker-*` Skill，并继承 `anki-cardmaker` 的先预览、后确认导入规则。
