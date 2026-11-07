#!/usr/bin/env python3
"""Check reachability of URL-backed vocabulary example sources.

This verifies URL reachability and source metadata shape only. It does not prove
that an example sentence came from the cited page.
"""

import argparse
import re
import sys
import urllib.error
import urllib.request

from card_validation import load_cards, is_strict_vocabulary_import


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def check_url(url, timeout):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "anki-cardmaker-source-check/1.0"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, ""
    except urllib.error.HTTPError as exc:
        if exc.code not in {403, 405, 501}:
            return exc.code, str(exc)
    except (urllib.error.URLError, TimeoutError) as exc:
        return None, str(exc)

    request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": "anki-cardmaker-source-check/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, ""
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        return getattr(exc, "code", None), str(exc)


def main():
    parser = argparse.ArgumentParser(description="Check URL-backed example sources without syncing to Anki.")
    parser.add_argument("--file", required=True, help="Path to JSON file containing cards.")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP timeout in seconds (default: 8).")
    args = parser.parse_args()

    try:
        cards = load_cards(args.file)
    except Exception as exc:
        print(f"Error loading cards: {exc}", file=sys.stderr)
        return 1

    checked = 0
    failures = []
    for index, card in enumerate(cards, start=1):
        if not is_strict_vocabulary_import(card) or card.get("source_status") != "verified":
            continue
        sources = card.get("example_sources") or []
        for source in sources:
            urls = URL_PATTERN.findall(source)
            if not urls:
                failures.append(f"Card {index}: verified source has no URL for automatic checking: {source}")
                continue
            for url in urls:
                checked += 1
                status, detail = check_url(url.rstrip(".,);]"), args.timeout)
                if status is None or not 200 <= status < 400:
                    failures.append(f"Card {index}: {url} is not reachable ({status or detail})")
                else:
                    print(f"OK Card {index}: {url} ({status})")

    if failures:
        print("Source verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Source verification passed: {checked} URL(s) reachable.")
    print("Note: this checks URL reachability and metadata shape, not semantic provenance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
