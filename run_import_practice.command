#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"
python3 scripts/anki_sync.py --file examples/cards.practice.json --deck "AnkiCardmaker"
