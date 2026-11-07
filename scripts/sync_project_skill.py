#!/usr/bin/env python3
"""Validate, compare, or install the repository's Anki Skills."""

import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "MANIFEST.json"
IGNORED_PARTS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".pyd"}


def load_manifest():
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read package manifest {MANIFEST_PATH}: {exc}") from exc
    required = {"format_version", "name", "main_files", "main_directories", "callable_skills", "install_root", "symlink_aliases"}
    missing = sorted(required - manifest.keys())
    if missing:
        raise SystemExit(f"Package manifest is missing fields: {', '.join(missing)}")
    if manifest["format_version"] != 1:
        raise SystemExit(f"Unsupported manifest format_version: {manifest['format_version']}")
    return manifest


MANIFEST = load_manifest()
INSTALL_ROOT = Path(MANIFEST["install_root"].replace("~", str(Path.home()), 1))
CALLABLE_SKILLS = tuple(MANIFEST["callable_skills"])


def files_under(base):
    if not base.exists():
        return set()
    return {
        path.relative_to(base)
        for path in base.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.parts)
        and path.suffix not in IGNORED_SUFFIXES
    }


def project_sources():
    """Yield (label, relative-path-to-source mapping, installed target)."""
    main_files = {Path(item): ROOT / item for item in MANIFEST["main_files"]}
    for relative in MANIFEST["main_directories"]:
        source_root = ROOT / relative
        main_files.update(
            {Path(relative) / item: source_root / item for item in files_under(source_root)}
        )
    yield "anki-cardmaker", main_files, INSTALL_ROOT / "anki-cardmaker"
    for name in CALLABLE_SKILLS:
        skill_root = ROOT / "skills" / name
        files = {item: skill_root / item for item in files_under(skill_root)}
        yield name, files, INSTALL_ROOT / name


def validate_package():
    errors = []
    for relative in MANIFEST["main_files"]:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
    for relative in MANIFEST["main_directories"]:
        path = ROOT / relative
        if not path.is_dir():
            errors.append(f"missing required directory: {path.relative_to(ROOT)}")
    if not (ROOT / "skills").is_dir():
        errors.append("missing required directory: skills")
    for name in CALLABLE_SKILLS:
        skill_root = ROOT / "skills" / name
        for required in ("SKILL.md", "agents/openai.yaml"):
            path = skill_root / required
            if not path.is_file():
                errors.append(f"missing callable Skill file: {path.relative_to(ROOT)}")
    return errors


def compare_tree(source_files, target_root, label):
    differences = []
    target_files = files_under(target_root)
    for relative in sorted(set(source_files) | target_files, key=str):
        source_path = source_files.get(relative)
        target_path = target_root / relative
        if source_path is None:
            differences.append(f"installed-only: {label}/{relative}")
        elif not target_path.is_file():
            differences.append(f"missing installed file: {label}/{relative}")
        elif not filecmp.cmp(source_path, target_path, shallow=False):
            differences.append(f"different: {label}/{relative}")
    return differences


def installed_differences():
    differences = []
    for label, source_files, target in project_sources():
        differences.extend(compare_tree(source_files, target, label))
    for alias, relative_target in MANIFEST["symlink_aliases"].items():
        link = INSTALL_ROOT / alias
        expected = INSTALL_ROOT / relative_target
        if not link.is_symlink():
            differences.append(f"missing symlink: {alias} -> {relative_target}")
        else:
            actual_path = Path(link.readlink())
            actual = (link.parent / actual_path).resolve() if not actual_path.is_absolute() else actual_path.resolve()
            if actual != expected.resolve():
                differences.append(f"wrong symlink target: {alias} -> {link.readlink()}")
    return differences


def sync_tree(source_files, target_root):
    if target_root.is_symlink():
        raise SystemExit(f"Refusing to follow a symlink install directory: {target_root}")
    target_root.mkdir(parents=True, exist_ok=True)

    for relative, source in source_files.items():
        target = target_root / relative
        if target.is_symlink():
            raise SystemExit(f"Refusing to overwrite a symlink inside the install: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    installed_files = files_under(target_root)
    for relative in installed_files - set(source_files):
        target = target_root / relative
        if target.is_symlink():
            raise SystemExit(f"Refusing to remove a symlink inside the install: {target}")
        target.unlink()
    for directory in sorted((path for path in target_root.rglob("*") if path.is_dir() and not path.is_symlink()), key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def install():
    errors = validate_package()
    if errors:
        raise SystemExit("Package validation failed:\n- " + "\n- ".join(errors))
    for _label, source_files, target in project_sources():
        sync_tree(source_files, target)
    differences = installed_differences()
    if differences:
        raise SystemExit("Install verification failed:\n- " + "\n- ".join(differences))
    print(f"Installed {MANIFEST['name']} and {len(CALLABLE_SKILLS)} callable Skills to {INSTALL_ROOT}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true", help="Validate the repository package (default).")
    actions.add_argument("--check-installed", action="store_true", help="Compare the package with ~/.codex/skills without writing.")
    actions.add_argument("--install", action="store_true", help="Install the package and callable Skills.")
    args = parser.parse_args()

    errors = validate_package()
    if errors:
        print("Package validation failed:", file=sys.stderr)
        print("\n".join(f"- {item}" for item in errors), file=sys.stderr)
        raise SystemExit(1)

    if args.install:
        install()
    elif args.check_installed:
        differences = installed_differences()
        if differences:
            print("Installed Skill drift detected:")
            print("\n".join(f"- {item}" for item in differences))
            raise SystemExit(1)
        print("Installed Skills and Chinese symlink aliases match the project package.")
    else:
        print(f"Package manifest and {len(CALLABLE_SKILLS)} callable Skills are valid.")


if __name__ == "__main__":
    main()
