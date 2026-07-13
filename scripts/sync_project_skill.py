#!/usr/bin/env python3
"""Sync the project-local debug Skill into the repository publish tree."""

import argparse
import filecmp
import shutil
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1] if (HERE.parents[1] / ".agents").exists() else HERE.parents[4]
PROJECT_SKILL = ROOT / ".agents" / "skills" / "anki-cardmaker"
PUBLISH_FILES = ("SKILL.md", "VERSION")
DIRECTORIES = ("scripts", "schemas", "examples", "subskills")
CALLABLE_SKILLS = (
    "anki-cardmaker-vocabulary",
    "anki-cardmaker-cloze",
    "anki-cardmaker-single-choice",
    "anki-cardmaker-multiple-choice",
    "anki-cardmaker-true-false",
    "anki-cardmaker-short-answer",
)


def files_under(base):
    if not base.exists():
        return set()
    return {p.relative_to(base) for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def drift():
    differences = []
    for name in PUBLISH_FILES:
        source, target = PROJECT_SKILL / name, ROOT / name
        if not source.exists():
            differences.append(f"missing project source: {source}")
        elif not target.exists() or not filecmp.cmp(source, target, shallow=False):
            differences.append(f"different: {source} -> {target}")
    for directory in DIRECTORIES:
        source_root, target_root = PROJECT_SKILL / directory, ROOT / directory
        for relative in sorted(files_under(source_root) | files_under(target_root)):
            source, target = source_root / relative, target_root / relative
            if not source.exists():
                differences.append(f"publish-only: {target}")
            elif not target.exists() or not filecmp.cmp(source, target, shallow=False):
                differences.append(f"different: {source} -> {target}")
    for skill_name in CALLABLE_SKILLS:
        source_root = ROOT / ".agents" / "skills" / skill_name
        target_root = ROOT / "skills" / skill_name
        for relative in sorted(files_under(source_root) | files_under(target_root)):
            source, target = source_root / relative, target_root / relative
            if not source.exists():
                differences.append(f"publish-only: {target}")
            elif not target.exists() or not filecmp.cmp(source, target, shallow=False):
                differences.append(f"different: {source} -> {target}")
    return differences


def sync():
    if not PROJECT_SKILL.exists():
        raise SystemExit(f"Project Skill not found: {PROJECT_SKILL}")
    for name in PUBLISH_FILES:
        source, target = PROJECT_SKILL / name, ROOT / name
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for directory in DIRECTORIES:
        source_root, target_root = PROJECT_SKILL / directory, ROOT / directory
        source_files, target_files = files_under(source_root), files_under(target_root)
        for relative in source_files:
            source, target = source_root / relative, target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in target_files - source_files:
            (target_root / relative).unlink()
    for skill_name in CALLABLE_SKILLS:
        source_root = ROOT / ".agents" / "skills" / skill_name
        target_root = ROOT / "skills" / skill_name
        source_files, target_files = files_under(source_root), files_under(target_root)
        for relative in source_files:
            source, target = source_root / relative, target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in target_files - source_files:
            (target_root / relative).unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without copying files.")
    args = parser.parse_args()
    if args.check:
        differences = drift()
        if differences:
            print("Project Skill and publish tree are out of sync:")
            print("\n".join(f"- {item}" for item in differences))
            raise SystemExit(1)
        print("Project Skill and publish tree are in sync.")
        return
    sync()
    print("Synced project-local Skill to the publish tree.")


if __name__ == "__main__":
    main()
