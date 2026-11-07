# Anki 制卡 Skill

本仓库用于独立维护 Anki 制卡 Skill。当前源文件以已安装的 `1.5.1` 版本为迁移基线。

## 目录

- 根目录的 `SKILL.md`、`agents/`、`scripts/`、`schemas/`、`examples/`、`subskills/` 和 `VERSION` 构成主 Skill，也是唯一源码和发布包。
- `skills/` 保存可独立调用的入口和题型 Skill。
- `MANIFEST.json` 列出主 Skill 文件、独立 Skill 和兼容入口。
- `~/.codex/skills/` 是运行时安装位置；仓库源文件才是后续开发的维护来源。

## 检查与安装

- `python3 scripts/sync_project_skill.py --check` 检查项目清单和必需文件。
- `python3 scripts/sync_project_skill.py --check-installed` 只读比较安装副本，并核对现有中文符号链接。
- `python3 scripts/sync_project_skill.py --install` 同步安装副本；只在用户明确要求更新时运行。

功能开发应在基于 `main` 的独立 `codex/` 分支和 worktree 中进行。不要直接修改或手工修补 `~/.codex/skills/`。
