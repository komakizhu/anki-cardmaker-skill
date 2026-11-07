#!/usr/bin/env python3
"""Regression tests for routing, validation, stage propagation, and HTML contracts."""

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve()
SCRIPT_DIR = HERE.parent
SKILL_DIR = SCRIPT_DIR.parent
EXAMPLES_DIR = SKILL_DIR / "examples"
SNAPSHOT_DIR = EXAMPLES_DIR / "snapshots"
sys.path.insert(0, str(SCRIPT_DIR))

from anki_sync import (  # noqa: E402
    CHOICE_MODEL_FIELDS,
    CHOICE_MODEL_NAME,
    CHOICE_MODEL_TEMPLATES,
    DEFAULT_ANKI_CONNECT_URLS,
    build_style_block,
    choice_answer_display,
    choice_answer_letters,
    choice_session_id,
    ensure_choice_model,
    format_links_and_images,
    sync_cards,
)
from card_validation import infer_question_type, validate_cards  # noqa: E402
from preview_cards import render_preview  # noqa: E402
from sync_project_skill import compare_tree, sync_tree  # noqa: E402


VOCAB_FIXTURE = EXAMPLES_DIR / "cards.screenshot.kaoyan2.2026-07.full.json"
CHOICE_FIXTURE = EXAMPLES_DIR / "choice-interactions.json"


def read_snapshot(name):
    path = SNAPSHOT_DIR / name
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def load_vocab_fixture():
    return json.loads(VOCAB_FIXTURE.read_text(encoding="utf-8"))[0]


def load_choice_fixture():
    return json.loads(CHOICE_FIXTURE.read_text(encoding="utf-8"))


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

    def test_choice_fixture_covers_all_supported_interactive_types(self):
        cards = load_choice_fixture()
        self.assertEqual(validate_cards(cards), [])
        self.assertEqual(
            [infer_question_type(card) for card in cards],
            ["single_choice", "multiple_choice", "true_false"],
        )

    def test_choice_front_and_back_keep_one_complete_question_surface(self):
        for card in load_choice_fixture():
            with self.subTest(question_type=card["question_type"]):
                front_html, back_html = format_links_and_images(card, {}, include_mathjax=False)
                for rendered in (front_html, back_html):
                    self.assertIn(card["front"], rendered)
                    for option in card["options"]:
                        self.assertIn(option, rendered)
                    self.assertEqual(rendered.count('class="anki-card-container anki-choice-card"'), 1)
                    self.assertNotIn("{{FrontSide}}", rendered)
                    self.assertNotIn("FrontSide", rendered)
                self.assertIn('<button type="button" class="anki-choice-option"', front_html)
                self.assertIn('aria-pressed="false"', front_html)
                if card["question_type"] == "multiple_choice":
                    self.assertIn('<button type="button" class="anki-choice-submit"', front_html)
                else:
                    self.assertNotIn('<button type="button" class="anki-choice-submit"', front_html)
                self.assertIn("anki-choice-option--correct", back_html)
                self.assertIn("未作答", back_html)
                self.assertIn(card["explanation"], back_html)

    def test_choice_answer_sets_and_stable_session_ids(self):
        cards = load_choice_fixture()
        self.assertEqual(choice_answer_letters(cards[0]), ["B"])
        self.assertEqual(choice_answer_letters(cards[1]), ["A", "B", "C"])
        self.assertEqual(choice_answer_letters(cards[2]), ["B"])
        self.assertEqual(choice_answer_display(cards[1]), "A. Red; B. Green; C. Blue")
        self.assertEqual(choice_session_id(cards[0]), choice_session_id(copy.deepcopy(cards[0])))
        edited = copy.deepcopy(cards[0])
        edited["front"] += "?"
        self.assertNotEqual(choice_session_id(cards[0]), choice_session_id(edited))

    def test_choice_interaction_contract_has_no_global_keyboard_capture(self):
        cards = load_choice_fixture()
        for card in cards:
            front_html, back_html = format_links_and_images(card, {}, include_mathjax=False)
            combined = front_html + back_html
            self.assertIn("sessionStorage", combined)
            self.assertIn("aria-live=\"polite\"", combined)
            self.assertIn('window.setTimeout(function()', combined)
            self.assertIn("450", combined)
            self.assertIn("MutationObserver", combined)
            self.assertIn("onUpdateHook", combined)
            self.assertIn("event.detail === 0", combined)
            self.assertIn("if (!requested) addManualRevealHint(root)", combined)
            self.assertIn('window.pycmd("ans")', combined)
            self.assertIn("window.showAnswer()", combined)
            self.assertNotIn("keydown", combined.lower())
            self.assertNotIn("document.write", combined.lower())
        multiple_front, _ = format_links_and_images(cards[1], {}, include_mathjax=False)
        self.assertIn("selected.filter", multiple_front)
        self.assertIn("answer.length === correct.length", multiple_front)
        self.assertIn("anki-choice-option--incorrect", build_style_block())
        self.assertIn("anki-choice-option--correct", build_style_block())

    def test_choice_answer_model_is_private_and_uses_isolated_templates(self):
        self.assertEqual(DEFAULT_ANKI_CONNECT_URLS, ("http://127.0.0.1:8767", "http://localhost:8767"))
        responses = {
            "modelNames": [],
            "modelFieldNames": list(CHOICE_MODEL_FIELDS),
            "modelTemplates": CHOICE_MODEL_TEMPLATES,
        }
        calls = []

        def fake_request(action, **params):
            calls.append((action, params))
            return responses.get(action)

        with patch("anki_sync.request", side_effect=fake_request):
            ensure_choice_model()

        create_call = next(params for action, params in calls if action == "createModel")
        self.assertEqual(create_call["modelName"], CHOICE_MODEL_NAME)
        self.assertEqual(create_call["inOrderFields"], ["Front", "Back"])
        self.assertEqual(
            create_call["cardTemplates"],
            [{"Name": "Choice Card", "Front": "{{Front}}", "Back": "{{Back}}"}],
        )

    def test_choice_model_mismatch_is_not_overwritten(self):
        calls = []

        def fake_request(action, **params):
            calls.append(action)
            if action == "modelNames":
                return [CHOICE_MODEL_NAME]
            if action == "modelFieldNames":
                return ["Front", "Back", "Extra"]
            return {"Choice Card": {"Front": "{{Front}}", "Back": "{{Back}}"}}

        with patch("anki_sync.request", side_effect=fake_request):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    ensure_choice_model()
        self.assertNotIn("createModel", calls)

    def test_choice_model_is_verified_before_deck_creation(self):
        events = []
        with patch("anki_sync.ensure_choice_model", side_effect=lambda _urls: events.append("model")):
            with patch("anki_sync.ensure_deck_exists", side_effect=lambda _deck, _urls: events.append("deck")):
                with patch("anki_sync.request", side_effect=lambda action, **_params: events.append(action) or [123]):
                    sync_cards([load_choice_fixture()[0]], "Test", dry_run=False)
        self.assertEqual(events, ["model", "deck", "addNotes"])

    def test_qa_and_cloze_keep_their_existing_note_models(self):
        qa_card = {
            "type": "QA",
            "question_type": "short_answer",
            "front": "What is the capital of France?",
            "back": "Paris",
        }
        cloze_card = {
            "type": "Cloze",
            "question_type": "cloze",
            "input_shape": "passage_blank",
            "front": "Paris {{c1::lies along the Seine}}.",
            "back": "lies along the Seine",
        }
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            sync_cards([qa_card, cloze_card, load_choice_fixture()[0]], "Test", dry_run=True)
        self.assertIn("Type: Basic", output.getvalue())
        self.assertIn("Type: Cloze", output.getvalue())
        self.assertIn(f"Type: {CHOICE_MODEL_NAME}", output.getvalue())

    def test_choice_preview_has_flip_controls_and_single_surface(self):
        html = render_preview(load_choice_fixture())
        self.assertEqual(html.count('class="card choice-preview"'), len(load_choice_fixture()))
        self.assertIn("data-preview-flip", html)
        self.assertIn("data-preview-reset", html)
        self.assertIn('window.showAnswer = function()', html)
        self.assertIn(".choice-preview-face--back", html)

    def test_package_sync_preserves_manifest_relative_paths(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source = temporary_root / "source" / "agents" / "openai.yaml"
            source.parent.mkdir(parents=True)
            source.write_text("name: example\n", encoding="utf-8")
            target = temporary_root / "installed"
            source_files = {Path("agents/openai.yaml"): source}

            sync_tree(source_files, target)

            self.assertTrue((target / "agents" / "openai.yaml").is_file())
            self.assertEqual(compare_tree(source_files, target, "example"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
