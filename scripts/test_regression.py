#!/usr/bin/env python3
"""Regression tests for routing, validation, stage propagation, and HTML contracts."""

import copy
import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
SCRIPT_DIR = HERE.parent
SKILL_DIR = SCRIPT_DIR.parent
EXAMPLES_DIR = SKILL_DIR / "examples"
SNAPSHOT_DIR = EXAMPLES_DIR / "snapshots"
sys.path.insert(0, str(SCRIPT_DIR))

from anki_sync import build_style_block, format_links_and_images  # noqa: E402
from card_validation import infer_question_type, validate_cards  # noqa: E402


VOCAB_FIXTURE = EXAMPLES_DIR / "cards.screenshot.kaoyan2.2026-07.full.json"


def read_snapshot(name):
    path = SNAPSHOT_DIR / name
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def load_vocab_fixture():
    return json.loads(VOCAB_FIXTURE.read_text(encoding="utf-8"))[0]


class RegressionTests(unittest.TestCase):
    def test_isolated_word_list_routes_to_vocabulary_meaning(self):
        card = {
            "type": "QA",
            "input_shape": "isolated_vocabulary_list",
            "word": "harbor",
            "front": "She continued to **harbor** resentment.",
        }
        self.assertEqual(infer_question_type(card), "vocabulary_meaning")

    def test_isolated_word_list_cannot_route_to_cloze(self):
        card = {
            "type": "Cloze",
            "question_type": "cloze",
            "input_shape": "isolated_vocabulary_list",
            "front": "She continued to {{c1::harbor}} resentment.",
        }
        errors = validate_cards([card])
        self.assertTrue(any("isolated vocabulary lists must use" in error for error in errors), errors)

    def test_learning_stage_is_carried_into_generated_example_sources(self):
        card = load_vocab_fixture()
        self.assertEqual(validate_cards([card]), [])
        card = copy.deepcopy(card)
        card["example_sources"][1] = "自拟·阶段匹配例句"
        errors = validate_cards([card])
        self.assertTrue(any("learning stage" in error for error in errors), errors)

    def test_example_sources_must_align_one_to_one(self):
        card = copy.deepcopy(load_vocab_fixture())
        card["example_sources"].pop()
        errors = validate_cards([card])
        self.assertTrue(any("example_sources must align one-to-one" in error for error in errors), errors)

    def test_audio_html_snapshot(self):
        card = load_vocab_fixture()
        front_html, back_html = format_links_and_images(
            card,
            {"__audio__:defy": "anki_word_defy.mp3"},
            include_mathjax=False,
        )
        html = front_html + back_html
        for expected in read_snapshot("audio-card.html.snapshot"):
            self.assertIn(expected, html)

    def test_mobile_html_snapshot(self):
        html = build_style_block()
        for expected in read_snapshot("mobile-card.html.snapshot"):
            self.assertIn(expected, html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
