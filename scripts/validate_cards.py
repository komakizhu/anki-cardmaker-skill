#!/usr/bin/env python3
import argparse
import sys

from card_validation import load_cards, validate_cards


def main():
    parser = argparse.ArgumentParser(description="Validate generated Anki cards without syncing them.")
    parser.add_argument("--file", required=True, help="Path to JSON file containing cards.")
    args = parser.parse_args()

    try:
        cards = load_cards(args.file)
    except Exception as exc:
        print(f"Error loading cards: {exc}", file=sys.stderr)
        sys.exit(1)

    errors = validate_cards(cards)

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Validation passed for {len(cards)} cards.")


if __name__ == "__main__":
    main()
