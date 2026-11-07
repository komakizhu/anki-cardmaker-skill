# Anki 制卡 Skill

本仓库用于独立维护 Anki 制卡 Skill。当前源文件以已安装的 `1.5.1` 版本为迁移基线。

## 目录

- 根目录的 `SKILL.md`、`agents/`、`scripts/`、`schemas/`、`examples/`、`subskills/` 和 `VERSION` 构成主 Skill。
- `skills/` 保存可独立调用的入口和题型 Skill。
- `~/.codex/skills/` 是运行时安装位置；仓库源文件才是后续开发的维护来源。

功能开发应在基于 `main` 的独立 `codex/` 分支和 worktree 中进行。安装目录只通过明确的安装操作更新。
