#!/usr/bin/env python3
import json
import os
import re

DEFAULT_TAGS = ["anki-agent"]
SUPPORTED_TYPES = {"QA", "Cloze", "Choice"}
VOCABULARY_TAGS = {"vocabulary", "english", "ielts", "polysemy", "熟词僻义", "词汇"}
POS_PATTERN = re.compile(r"(?:^|\s)(?:n|v|adj|adv|prep|pron|conj|det|aux|modal|phr\. v)\.", re.IGNORECASE)
CLOZE_PATTERN = re.compile(r"\{\{c\d+::([^{}:]+)(?::[^{}]*)?\}\}", re.IGNORECASE)
ENGLISH_WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z'-]*$")
MEANING_QUESTION_PATTERN = re.compile(r"(?:definition|meaning)\s+of\s+['\"“‘][^'\"”’]+['\"”’]", re.IGNORECASE)


def load_cards(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data

    raise ValueError("Input JSON must be a card object or a list of card objects")


def normalize_card_type(card_type):
    mapping = {
        "qa": "QA",
        "basic": "QA",
        "cloze": "Cloze",
        "choice": "Choice",
    }
    raw = str(card_type or "QA").strip().lower()
    return mapping.get(raw, str(card_type or "QA").strip())


def normalize_tags(tags):
    if tags is None:
        values = list(DEFAULT_TAGS)
    elif isinstance(tags, str):
        values = [tags]
    elif isinstance(tags, (list, tuple, set)):
        values = list(tags)
    else:
        values = [tags]

    normalized = []
    seen = set()
    for tag in values:
        text = str(tag).strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)

    return normalized or list(DEFAULT_TAGS)


def contains_cjk(value):
    return bool(re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", str(value or "")))


def is_chinese_question(card):
    return normalize_card_type(card.get("type")) == "QA" and contains_cjk(card.get("front", ""))


def extract_cloze_targets(front):
    return [match.group(1).strip() for match in CLOZE_PATTERN.finditer(str(front or ""))]


def is_vocabulary_card(card):
    card_type = normalize_card_type(card.get("type"))
    word = str(card.get("word", "") or "").strip()
    if word:
        return True
    tags = {tag.lower() for tag in normalize_tags(card.get("tags"))}
    if tags & VOCABULARY_TAGS:
        return True
    front = str(card.get("front", "") or "")
    if card_type == "Cloze":
        targets = extract_cloze_targets(front)
        return len(targets) == 1 and bool(ENGLISH_WORD_PATTERN.fullmatch(targets[0]))
    return bool(MEANING_QUESTION_PATTERN.search(front))


def validate_relation_items(value, prefix, field_name):
    """Vocabulary relation entries need a lexical item, POS, and Chinese gloss."""
    errors = []
    if value is None:
        return errors
    items = [value] if isinstance(value, str) else list(value) if isinstance(value, (list, tuple, set)) else []
    if not items:
        return errors
    for item in items:
        text = str(item).strip()
        if not POS_PATTERN.search(text) or not contains_cjk(text):
            errors.append(
                f"{prefix}: '{field_name}' entries must include a part of speech and Chinese meaning"
            )
            break
    return errors


def validate_source(source, prefix):
    errors = []
    if source is None:
        return errors
    if not isinstance(source, dict):
        return [f"{prefix}: 'source' must be an object"]

    allowed = {"title", "url", "file", "page", "chapter"}
    for key, value in source.items():
        if key not in allowed:
            continue
        if key in {"title", "url", "file", "chapter"} and value is not None and not isinstance(value, str):
            errors.append(f"{prefix}: source.{key} must be a string")
        if key == "page" and value is not None and not isinstance(value, (int, str)):
            errors.append(f"{prefix}: source.page must be a string or integer")

    return errors


def validate_string_or_string_list(value, prefix, field_name):
    errors = []
    if value is None:
        return errors
    if isinstance(value, str):
        return errors
    if isinstance(value, (list, tuple, set)):
        invalid = [item for item in value if not isinstance(item, str)]
        if invalid:
            errors.append(f"{prefix}: '{field_name}' must contain only strings")
        return errors
    errors.append(f"{prefix}: '{field_name}' must be a string or a list of strings")
    return errors


def validate_card(card, index):
    errors = []
    prefix = f"Card {index + 1}"

    if not isinstance(card, dict):
        return [f"{prefix}: expected an object, got {type(card).__name__}"]

    if "schema_version" in card and not isinstance(card["schema_version"], str):
        errors.append(f"{prefix}: 'schema_version' must be a string")

    card_type = normalize_card_type(card.get("type"))
    if card_type not in SUPPORTED_TYPES:
        errors.append(f"{prefix}: unsupported type '{card.get('type')}'")

    front = card.get("front")
    if not isinstance(front, str) or not front.strip():
        errors.append(f"{prefix}: missing or empty 'front'")

    if card_type == "QA":
        back = card.get("back")
        back_zh = card.get("back_zh")
        if is_chinese_question(card) and not is_vocabulary_card(card):
            if not isinstance(back_zh, str) or not back_zh.strip():
                errors.append(f"{prefix}: Chinese QA cards require a non-empty 'back_zh'")
        elif not isinstance(back, str) or not back.strip():
            errors.append(f"{prefix}: QA cards require a non-empty 'back'")
    elif card_type == "Choice":
        options = card.get("options")
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"{prefix}: Choice cards require at least two options")
        else:
            invalid_options = [opt for opt in options if not isinstance(opt, str) or not opt.strip()]
            if invalid_options:
                errors.append(f"{prefix}: Choice options must be non-empty strings")
            if len(options) > 26:
                errors.append(f"{prefix}: Choice cards support at most 26 options")

        correct_answer = card.get("correct_answer")
        if not isinstance(correct_answer, str) or not correct_answer.strip():
            errors.append(f"{prefix}: Choice cards require a non-empty 'correct_answer'")
        elif isinstance(options, list) and options:
            letters = re.findall(r"[A-Za-z]+", correct_answer.upper())
            if letters and all(len(letter) == 1 for letter in letters):
                invalid = [letter for letter in letters if ord(letter) - 65 >= len(options)]
                if invalid:
                    errors.append(f"{prefix}: correct_answer refers to unavailable option(s): {', '.join(invalid)}")
    else:
        back = card.get("back")
        if back is not None and not isinstance(back, str):
            errors.append(f"{prefix}: 'back' must be a string when present")

    tags = card.get("tags")
    if tags is not None and not isinstance(tags, (list, tuple, set, str)):
        errors.append(f"{prefix}: 'tags' must be a string or a list of strings")
    elif isinstance(tags, (list, tuple, set)) and any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        errors.append(f"{prefix}: 'tags' must contain only non-empty strings")

    explanation = card.get("explanation")
    if explanation is not None and not isinstance(explanation, str):
        errors.append(f"{prefix}: 'explanation' must be a string when present")

    explanation_zh = card.get("explanation_zh")
    if explanation_zh is not None and not isinstance(explanation_zh, str):
        errors.append(f"{prefix}: 'explanation_zh' must be a string when present")

    back_zh = card.get("back_zh")
    if back_zh is not None and not isinstance(back_zh, str):
        errors.append(f"{prefix}: 'back_zh' must be a string when present")

    mnemonic_hook_zh = card.get("mnemonic_hook_zh")
    if mnemonic_hook_zh is not None and not isinstance(mnemonic_hook_zh, str):
        errors.append(f"{prefix}: 'mnemonic_hook_zh' must be a string when present")

    for field_name in (
        "part_of_speech",
        "phonetic",
        "definition_zh",
        "word_level",
        "oxford_definition",
        "collins_definition",
        "oxford_definition_zh",
        "collins_definition_zh",
        "explanation_target_zh",
        "mnemonic_target_zh",
        "word_root",
        "word_affixes",
    ):
        value = card.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(f"{prefix}: '{field_name}' must be a string when present")

    word = card.get("word")
    if word is not None and (not isinstance(word, str) or not word.strip()):
        errors.append(f"{prefix}: 'word' must be a non-empty string when present")

    if is_vocabulary_card(card):
        for field_name in ("part_of_speech", "phonetic", "definition_zh", "word_level"):
            value = card.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: vocabulary cards require a non-empty '{field_name}'")

        for source_name, translation_name in (
            ("oxford_definition", "oxford_definition_zh"),
            ("collins_definition", "collins_definition_zh"),
        ):
            source_value = card.get(source_name)
            translation_value = card.get(translation_name)
            if source_value and (not isinstance(translation_value, str) or not translation_value.strip()):
                errors.append(f"{prefix}: '{source_name}' requires '{translation_name}'")

    for field_name in ("core_keywords", "synonyms", "antonyms", "contrast_terms"):
        errors.extend(validate_string_or_string_list(card.get(field_name), prefix, field_name))

    for field_name in ("near_synonyms", "confusable_words", "collocations", "other_meanings"):
        errors.extend(validate_string_or_string_list(card.get(field_name), prefix, field_name))

    if is_vocabulary_card(card):
        for field_name in ("synonyms", "antonyms", "near_synonyms", "confusable_words"):
            errors.extend(validate_relation_items(card.get(field_name), prefix, field_name))

    raw_other_meanings = card.get("other_meanings")
    if isinstance(raw_other_meanings, str):
        other_meanings = [item.strip() for item in raw_other_meanings.splitlines() if item.strip()]
    elif isinstance(raw_other_meanings, (list, tuple, set)):
        other_meanings = [str(item).strip() for item in raw_other_meanings if str(item).strip()]
    else:
        other_meanings = []
    other_meanings_examples = card.get("other_meanings_examples")
    if other_meanings and other_meanings_examples is None:
        errors.append(f"{prefix}: 'other_meanings' requires 'other_meanings_examples'")
    if other_meanings_examples is not None:
        if not isinstance(other_meanings_examples, list) or any(not isinstance(item, str) or not item.strip() for item in other_meanings_examples):
            errors.append(f"{prefix}: 'other_meanings_examples' must be a list of non-empty strings when present")
        elif len(other_meanings) != len(other_meanings_examples):
            errors.append(f"{prefix}: 'other_meanings_examples' must align one-to-one with 'other_meanings'")

    example_sentences = card.get("example_sentences")
    example_sentences_zh = card.get("example_sentences_zh")
    for field_name, value in (("example_sentences", example_sentences), ("example_sentences_zh", example_sentences_zh)):
        if value is not None:
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                errors.append(f"{prefix}: '{field_name}' must be a list of non-empty strings when present")
            elif len(value) < 3:
                errors.append(f"{prefix}: '{field_name}' must contain at least three items when present")

    if is_vocabulary_card(card) and any(value is not None for value in (example_sentences, example_sentences_zh, card.get("example_targets_zh"))):
        if not isinstance(example_sentences, list) or not isinstance(example_sentences_zh, list):
            errors.append(f"{prefix}: vocabulary bilingual examples require both example sentence lists")
        elif len(example_sentences) != len(example_sentences_zh):
            errors.append(f"{prefix}: example_sentences and example_sentences_zh must have equal lengths")

    example_targets_zh = card.get("example_targets_zh")
    if example_targets_zh is not None:
        if not isinstance(example_targets_zh, list) or any(not isinstance(item, str) or not item.strip() for item in example_targets_zh):
            errors.append(f"{prefix}: 'example_targets_zh' must be a list of non-empty strings when present")
        elif example_sentences_zh is not None and len(example_targets_zh) != len(example_sentences_zh):
            errors.append(f"{prefix}: 'example_targets_zh' must align one-to-one with 'example_sentences_zh'")
    if is_vocabulary_card(card) and isinstance(example_sentences, list) and isinstance(example_sentences_zh, list):
        if len(example_targets_zh or []) != len(example_sentences_zh):
            errors.append(f"{prefix}: vocabulary bilingual examples require one example_targets_zh per translation")

    if card_type == "Cloze" and not extract_cloze_targets(front):
        errors.append(f"{prefix}: Cloze cards require at least one valid {{cN::...}} deletion")

    example_sentence = card.get("example_sentence")
    if example_sentence is not None and not isinstance(example_sentence, str):
        errors.append(f"{prefix}: 'example_sentence' must be a string when present")

    example_sentence_zh = card.get("example_sentence_zh")
    if example_sentence_zh is not None and not isinstance(example_sentence_zh, str):
        errors.append(f"{prefix}: 'example_sentence_zh' must be a string when present")

    source = card.get("source")
    errors.extend(validate_source(source, prefix))

    return errors


def validate_cards(cards):
    errors = []
    for idx, card in enumerate(cards):
        errors.extend(validate_card(card, idx))
    return errors
