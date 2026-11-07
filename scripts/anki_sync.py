#!/usr/bin/env python3
import argparse
import base64
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

from card_validation import infer_question_type, normalize_card_type, normalize_tags, validate_cards

DEFAULT_ANKI_CONNECT_URLS = ("http://127.0.0.1:8767", "http://localhost:8767")
DEFAULT_CLOZE_EXTRA_FIELD = "Back Extra"
DEFAULT_TAGS = ["anki-agent"]
CHOICE_MODEL_NAME = "AnkiCardmaker Choice"
CHOICE_MODEL_FIELDS = ("Front", "Back")
CHOICE_MODEL_TEMPLATE_NAME = "Choice Card"
CHOICE_MODEL_TEMPLATES = {
    CHOICE_MODEL_TEMPLATE_NAME: {"Front": "{{Front}}", "Back": "{{Back}}"}
}


def request(action, anki_urls=DEFAULT_ANKI_CONNECT_URLS, retries=3, retry_delay=0.3, **params):
    payload = {"action": action, "version": 6, "params": params}
    data = json.dumps(payload).encode("utf-8")
    last_error = None

    for attempt in range(1, retries + 1):
        for anki_url in anki_urls:
            req = urllib.request.Request(
                anki_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=3) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    if len(res) != 2:
                        raise Exception("Response has an unexpected number of fields")
                    if "error" not in res:
                        raise Exception("Response is missing required error field")
                    if "result" not in res:
                        raise Exception("Response is missing required result field")
                    if res["error"] is not None:
                        raise Exception(res["error"])
                    return res["result"]
            except urllib.error.URLError as e:
                last_error = e
            except Exception as e:
                print(f"AnkiConnect Error: {e}", file=sys.stderr)
                sys.exit(1)

        if attempt < retries:
            time.sleep(retry_delay)

    print(
        f"Error: Cannot connect to Anki at {', '.join(anki_urls)}. Is Anki running with AnkiConnect installed?",
        file=sys.stderr,
    )
    if last_error is not None:
        print(f"Last connection error: {last_error}", file=sys.stderr)
    sys.exit(1)


def ensure_deck_exists(deck_name, anki_urls):
    decks = request("deckNames", anki_urls=anki_urls)
    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found. Creating...")
        request("createDeck", anki_urls=anki_urls, deck=deck_name)


def ensure_choice_model(anki_urls=DEFAULT_ANKI_CONNECT_URLS):
    """Create the private Choice note model or refuse to alter an unknown one."""
    model_names = request("modelNames", anki_urls=anki_urls)
    if CHOICE_MODEL_NAME not in model_names:
        request(
            "createModel",
            anki_urls=anki_urls,
            modelName=CHOICE_MODEL_NAME,
            inOrderFields=list(CHOICE_MODEL_FIELDS),
            css=".card { font-family: sans-serif; font-size: 20px; text-align: left; }",
            isCloze=False,
            cardTemplates=[
                {
                    "Name": CHOICE_MODEL_TEMPLATE_NAME,
                    "Front": "{{Front}}",
                    "Back": "{{Back}}",
                }
            ],
        )

    fields = request("modelFieldNames", anki_urls=anki_urls, modelName=CHOICE_MODEL_NAME)
    templates = request("modelTemplates", anki_urls=anki_urls, modelName=CHOICE_MODEL_NAME)
    if fields != list(CHOICE_MODEL_FIELDS) or templates != CHOICE_MODEL_TEMPLATES:
        print(
            f"Error: Anki note model '{CHOICE_MODEL_NAME}' exists but does not match "
            "the required Front/Back fields and isolated templates. It was not changed.",
            file=sys.stderr,
        )
        sys.exit(1)


def choice_answer_letters(card):
    """Return valid option letters from common single- and multiple-answer forms."""
    answer = str(card.get("correct_answer", "") or "").strip()
    options = card.get("options", []) or []
    normalized = answer.upper()

    if re.fullmatch(r"[A-Z]+", normalized):
        candidates = list(normalized)
    elif re.fullmatch(r"[A-Z](?:\s*[,/&;、]\s*[A-Z]|\s+[A-Z])*", normalized):
        candidates = re.findall(r"[A-Z]", normalized)
    else:
        candidates = []

    if candidates:
        letters = []
        for letter in candidates:
            if ord(letter) - 65 < len(options) and letter not in letters:
                letters.append(letter)
        if letters:
            return letters

    answer_key = re.sub(r"\s+", " ", answer).casefold()
    for index, option in enumerate(options):
        if re.sub(r"\s+", " ", str(option)).strip().casefold() == answer_key:
            return [chr(65 + index)]
    return []


def choice_session_id(card):
    identity = {
        "question_type": infer_question_type(card),
        "front": card.get("front", ""),
        "options": card.get("options", []),
        "correct_answer": card.get("correct_answer", ""),
    }
    payload = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def choice_answer_display(card):
    options = card.get("options", []) or []
    letters = choice_answer_letters(card)
    if letters:
        return "; ".join(f"{letter}. {options[ord(letter) - 65]}" for letter in letters)
    return resolve_choice_answer(card)


def render_choice_surface(card, style_block, mathjax_block, face, support_html=""):
    question_type = infer_question_type(card)
    labels = {
        "single_choice": "单选题",
        "multiple_choice": "多选题",
        "true_false": "判断题",
    }
    options = card.get("options", []) or []
    correct_letters = choice_answer_letters(card)
    correct_set = set(correct_letters)
    session_id = choice_session_id(card)
    is_back = face == "back"

    option_parts = ['<div class="anki-choice-options" role="group">']
    for index, option in enumerate(options):
        letter = chr(65 + index)
        correct_class = " anki-choice-option--correct" if is_back and letter in correct_set else ""
        option_content = (
            f'<span class="anki-choice-option__letter">{letter}.</span>'
            f'<span class="anki-choice-option__text">{format_multiline_text(option)}</span>'
        )
        if is_back:
            option_parts.append(
                f'<div class="anki-choice-option{correct_class}" data-choice-letter="{letter}" '
                'aria-selected="false">'
                f'{option_content}</div>'
            )
        else:
            option_parts.append(
                f'<button type="button" class="anki-choice-option" data-choice-letter="{letter}" '
                'aria-pressed="false">'
                f'{option_content}</button>'
            )
    option_parts.append("</div>")
    if not is_back and question_type == "multiple_choice":
        option_parts.append(
            '<button type="button" class="anki-choice-submit" disabled aria-disabled="true">提交答案</button>'
        )

    feedback_text = (
        f'未作答。正确答案：{choice_answer_display(card)}'
        if is_back
        else ("请选择一个答案。" if question_type != "multiple_choice" else "请选择所有符合条件的选项，再提交。")
    )
    face_name = "back" if is_back else "front"
    support = f'<div class="anki-support">{support_html}</div>' if is_back and support_html else ""
    config = {
        "id": session_id,
        "key": f"ankiChoice:{session_id}",
        "face": face_name,
        "type": question_type,
        "correct": correct_letters,
        "correctAnswer": choice_answer_display(card),
    }
    config_json = json.dumps(config, ensure_ascii=True, separators=(",", ":"))
    config_attribute = html.escape(config_json, quote=True)
    root = (
        f'{style_block}{mathjax_block}'
        f'<div class="anki-card-container anki-choice-card" data-choice-id="{session_id}" '
        f'data-choice-face="{face_name}" data-choice-type="{question_type}" '
        f'data-choice-config="{config_attribute}">'
        '<div class="anki-shell">'
        f'<div class="anki-vocab-type">{labels.get(question_type, "选择题")}</div>'
        f'<div class="anki-question">{format_multiline_text(card.get("front", ""))}</div>'
        f'{"".join(option_parts)}'
        f'<div class="anki-choice-feedback" aria-live="polite">{format_multiline_text(feedback_text)}</div>'
        f'{support}'
        '</div></div>'
    )

    script = '''<script>
(function() {
  var activeScript = document.currentScript;
  var initialRoot = activeScript && activeScript.previousElementSibling;
  var selector = ".anki-choice-card";

  function readConfig(root) {
    if (!root) return null;
    try { return JSON.parse(root.getAttribute("data-choice-config") || ""); }
    catch (error) { return null; }
  }
  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }

  var controller = window.__ankiChoiceController;
  if (!controller) {
    var memory = window.__ankiChoiceState || (window.__ankiChoiceState = {});

    function contains(list, value) { return list.indexOf(value) !== -1; }
    function readState(config) {
      try {
        var value = window.sessionStorage.getItem(config.key);
        if (value) return JSON.parse(value);
      } catch (error) {}
      return memory[config.key] || null;
    }
    function writeState(config, value) {
      memory[config.key] = value;
      try { window.sessionStorage.setItem(config.key, JSON.stringify(value)); } catch (error) {}
    }
    function clearState(config) {
      delete memory[config.key];
      try { window.sessionStorage.removeItem(config.key); } catch (error) {}
    }
    function setClass(node, name, active) {
      if (active && !node.classList.contains(name)) node.classList.add(name);
      else if (!active && node.classList.contains(name)) node.classList.remove(name);
    }
    function updateOptions(root, config, selected, locked, showResult) {
      var optionNodes = root.querySelectorAll("[data-choice-letter]");
      var correct = config.correct || [];
      for (var i = 0; i < optionNodes.length; i++) {
        var node = optionNodes[i];
        var letter = node.getAttribute("data-choice-letter");
        var isSelected = contains(selected, letter);
        var isCorrect = contains(correct, letter);
        setClass(node, "anki-choice-option--selected", isSelected);
        setClass(node, "anki-choice-option--correct", showResult && isCorrect);
        setClass(node, "anki-choice-option--incorrect", showResult && isSelected && !isCorrect);
        if (node.tagName.toLowerCase() === "button") {
          if (node.disabled !== locked) node.disabled = locked;
          var pressed = isSelected ? "true" : "false";
          if (node.getAttribute("aria-pressed") !== pressed) node.setAttribute("aria-pressed", pressed);
        } else {
          var selectedValue = isSelected ? "true" : "false";
          if (node.getAttribute("aria-selected") !== selectedValue) node.setAttribute("aria-selected", selectedValue);
        }
      }
    }
    function renderBack(root, config, state) {
      var feedback = root.querySelector(".anki-choice-feedback");
      if (!feedback) return;
      var selected = state && Array.isArray(state.selected) ? state.selected : [];
      updateOptions(root, config, selected, true, true);
      if (!state) setText(feedback, "未作答。正确答案：" + config.correctAnswer);
      else if (state.correct) setText(feedback, "回答正确。正确答案：" + config.correctAnswer);
      else setText(feedback, "回答错误。你的选择：" + (selected.join("、") || "无") + "；正确答案：" + config.correctAnswer);
    }
    function refreshBacks(id) {
      var roots = document.querySelectorAll(selector + '[data-choice-face="back"]');
      for (var i = 0; i < roots.length; i++) {
        var root = roots[i];
        var config = readConfig(root);
        if (config && config.id === id) renderBack(root, config, readState(config));
      }
    }
    function announceAnswer(id) {
      try {
        window.dispatchEvent(new CustomEvent("anki-choice-preview-answer", { detail: { id: id } }));
      } catch (error) {}
    }
    function addManualRevealHint(root) {
      if (!document.documentElement.contains(root) || root.getAttribute("data-choice-face") !== "front") return;
      var bounds = root.getBoundingClientRect();
      if (!bounds.width || !bounds.height) return;
      var feedback = root.querySelector(".anki-choice-feedback");
      if (feedback && feedback.textContent.indexOf("按空格") === -1) {
        setText(feedback, feedback.textContent + " 按空格或使用“显示答案”查看解析。");
      }
    }
    function reveal(root, config, answer) {
      if (root.__ankiChoiceLocked || !answer.length) return;
      root.__ankiChoiceLocked = true;
      root.__ankiChoiceSelection = answer.slice();
      var correct = config.correct || [];
      var isCorrect = answer.length === correct.length && answer.every(function(letter) { return contains(correct, letter); });
      writeState(config, { selected: answer.slice(), correct: isCorrect });
      updateOptions(root, config, answer, true, true);
      var feedback = root.querySelector(".anki-choice-feedback");
      if (feedback) setText(feedback, isCorrect
        ? "回答正确。正确答案：" + config.correctAnswer
        : "回答错误。你的选择：" + answer.join("、") + "；正确答案：" + config.correctAnswer);
      window.__ankiActiveChoiceId = config.id;
      announceAnswer(config.id);
      window.setTimeout(function() {
        var requested = false;
        try {
          if (typeof window.pycmd === "function") {
            window.pycmd("ans");
            requested = true;
          } else if (typeof window.showAnswer === "function") {
            window.showAnswer();
            requested = true;
          }
        } catch (error) {}
        if (!requested) addManualRevealHint(root);
        else window.setTimeout(function() { addManualRevealHint(root); }, 900);
      }, 450);
    }
    function resetFront(root, config) {
      root.__ankiChoiceSelection = [];
      root.__ankiChoiceLocked = false;
      clearState(config);
      var submit = root.querySelector(".anki-choice-submit");
      if (submit) {
        submit.disabled = true;
        submit.setAttribute("aria-disabled", "true");
      }
      updateOptions(root, config, [], false, false);
      var feedback = root.querySelector(".anki-choice-feedback");
      if (feedback) setText(feedback, config.type === "multiple_choice"
        ? "请选择所有符合条件的选项，再提交。"
        : "请选择一个答案。");
    }
    function initialize(root, resetCurrentFront) {
      var config = readConfig(root);
      if (!config || !config.id || !config.key) return;
      var stamp = JSON.stringify(config);
      var changed = root.__ankiChoiceStamp !== stamp;
      if (changed) root.__ankiChoiceStamp = stamp;
      if (config.face === "front" && (changed || resetCurrentFront)) resetFront(root, config);
      else if (config.face === "back") renderBack(root, config, readState(config));
    }
    function inspectNode(node) {
      var element = node && (node.nodeType === 1 ? node : node.parentElement);
      if (!element) return;
      var parent = element.matches && element.matches(selector) ? element : (element.closest ? element.closest(selector) : null);
      if (parent) initialize(parent, false);
      if (element.querySelectorAll) {
        var descendants = element.querySelectorAll(selector);
        for (var i = 0; i < descendants.length; i++) initialize(descendants[i], false);
      }
    }
    function scan(resetCurrentFront) {
      var roots = document.querySelectorAll(selector);
      for (var i = 0; i < roots.length; i++) initialize(roots[i], resetCurrentFront);
    }
    function handleClick(event) {
      var target = event.target;
      if (!target || !target.closest) return;
      var option = target.closest("button[data-choice-letter]");
      var submit = target.closest("button.anki-choice-submit");
      if (!option && !submit) return;
      if (event.detail === 0) return;
      var root = (option || submit).closest(selector);
      var config = readConfig(root);
      if (!root || !config || config.face !== "front") return;
      event.preventDefault();
      event.stopPropagation();
      if (root.__ankiChoiceLocked) return;
      if (submit) {
        var submitted = root.__ankiChoiceSelection || [];
        if (submitted.length) reveal(root, config, submitted.slice());
        return;
      }
      var letter = option.getAttribute("data-choice-letter");
      if (config.type === "multiple_choice") {
        var selected = root.__ankiChoiceSelection || [];
        root.__ankiChoiceSelection = contains(selected, letter)
          ? selected.filter(function(item) { return item !== letter; })
          : selected.concat([letter]);
        updateOptions(root, config, root.__ankiChoiceSelection, false, false);
        var submitButton = root.querySelector(".anki-choice-submit");
        var enabled = root.__ankiChoiceSelection.length > 0;
        if (submitButton) {
          submitButton.disabled = !enabled;
          submitButton.setAttribute("aria-disabled", enabled ? "false" : "true");
        }
        var feedback = root.querySelector(".anki-choice-feedback");
        if (feedback) setText(feedback, enabled
          ? "已选择 " + root.__ankiChoiceSelection.join("、") + "。完成后提交答案。"
          : "请选择所有符合条件的选项，再提交。");
      } else reveal(root, config, [letter]);
    }
    var updateHook = function() { scan(true); };
    controller = {
      initialize: initialize,
      refreshBacks: refreshBacks,
      registerUpdateHook: function() {
        if (window.onUpdateHook && typeof window.onUpdateHook.push === "function" && window.onUpdateHook.indexOf(updateHook) === -1) {
          window.onUpdateHook.push(updateHook);
        }
      }
    };
    window.__ankiChoiceController = controller;
    document.addEventListener("click", handleClick, false);
    window.addEventListener("anki-choice-preview-answer", function(event) {
      if (event.detail && event.detail.id) refreshBacks(event.detail.id);
    }, false);
    if (typeof MutationObserver === "function" && document.documentElement) {
      var observer = new MutationObserver(function(records) {
        for (var i = 0; i < records.length; i++) {
          var record = records[i];
          if (record.type === "attributes") inspectNode(record.target);
          else for (var j = 0; j < record.addedNodes.length; j++) inspectNode(record.addedNodes[j]);
        }
      });
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["data-choice-id", "data-choice-face", "data-choice-config"]
      });
    }
  }

  if (initialRoot && initialRoot.getAttribute("data-choice-id")) {
    controller.initialize(initialRoot, initialRoot.getAttribute("data-choice-face") === "front");
  }
  controller.registerUpdateHook();
})();
</script>'''
    return root + script


def escape_text(value):
    return html.escape("" if value is None else str(value), quote=False)


def format_multiline_text(value):
    return escape_text(value).replace("\n", "<br>")


def build_mathjax_block():
    """Load MathJax for LaTeX found in card text and formula fields."""
    return (
        r'<script>window.MathJax = {tex: {inlineMath: [["\\(","\\)"],["$","$"]], displayMath: [["\\[","\\]"],["$$","$$"]], processEscapes: true}, svg: {fontCache: "global"}};</script>'
        '<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>'
    )


def build_style_block():
    return (
        '<style>'
        '.anki-card-container { '
        '  --anki-bg: #fbf8f2; '
        '  --anki-surface: #fdfbf7; '
        '  --anki-fg: #292725; '
        '  --anki-muted: #746d66; '
        '  --anki-border: #ded8ce; '
        '  --anki-accent: #a94b42; '
        '  display: flex; flex-direction: column; max-width: 900px; margin: 0 auto; padding: 26px 28px; '
        '  background: var(--anki-bg); border: 1px solid var(--anki-border); border-radius: 14px; '
        '  font-family: Georgia, "Times New Roman", Times, serif; '
        '  line-height: 1.68; '
        '  color: var(--anki-fg); '
        '}'
        '.anki-card-container, .anki-card-container * { box-sizing: border-box; }'
        '.anki-card-container, .anki-card-container * { color: inherit; }'
        '.anki-shell { display: flex; flex-direction: column; gap: 16px; }'
        '.anki-question { font-size: 22px; line-height: 1.55; font-weight: 700; color: var(--anki-fg); padding-bottom: 22px; border-bottom: 1px solid var(--anki-border); }'
        '.anki-vocab-type { width: 100%; text-align: left; font-size: 16px; line-height: 1.4; font-weight: 700; color: var(--anki-accent); }'
        '.anki-vocab-sentence { padding: 18px 0 22px; border-bottom: 1px solid var(--anki-border); font-size: 23px; line-height: 1.55; font-weight: 700; color: var(--anki-fg); }'
        '.anki-vocab-sentence strong { color: var(--anki-accent); }'
        '.anki-options-list { list-style-type: none; padding-left: 0; margin: 18px 0 0; display: grid; gap: 10px; }'
        '.anki-options-list li { padding: 13px 15px; border-radius: 9px; border: 1px solid var(--anki-border); background: var(--anki-surface); color: var(--anki-fg); }'
        '.anki-options-list strong { color: var(--anki-fg); }'
        '.anki-choice-options { display: grid; gap: 10px; margin-top: 18px; }'
        '.anki-choice-option { display: flex; gap: 10px; align-items: flex-start; width: 100%; padding: 13px 15px; border: 1px solid var(--anki-border); border-radius: 9px; background: var(--anki-surface); color: var(--anki-fg); font: inherit; line-height: 1.5; text-align: left; cursor: pointer; }'
        'button.anki-choice-option:focus-visible, .anki-choice-submit:focus-visible { outline: 3px solid #2563eb; outline-offset: 2px; }'
        '.anki-choice-option__letter { flex: 0 0 auto; font-weight: 700; }'
        '.anki-choice-option--selected { border-color: var(--anki-accent); box-shadow: 0 0 0 1px var(--anki-accent) inset; }'
        '.anki-choice-option--correct { border-color: #338454; background: #e8f5ec; color: #1b6339; font-weight: 700; }'
        '.anki-choice-option--incorrect { border-color: #c43c3c; background: #fdeaea; color: #942525; font-weight: 700; }'
        '.anki-choice-submit { align-self: flex-start; margin-top: 4px; padding: 10px 18px; border: 0; border-radius: 8px; background: var(--anki-accent); color: #fff; font: inherit; font-weight: 700; cursor: pointer; }'
        '.anki-choice-submit:disabled { opacity: .5; cursor: not-allowed; }'
        '.anki-choice-feedback { min-height: 1.6em; color: var(--anki-muted); font-size: 15px; font-weight: 700; }'
        '.anki-answer { display: flex; flex-direction: column; gap: 8px; }'
        '.anki-answer-title { width: 100%; text-align: left; align-self: flex-start; font-size: 15px; line-height: 1.4; font-weight: 700; color: var(--anki-accent); }'
        '.anki-answer-main { font-size: 20px; line-height: 1.55; color: var(--anki-fg); font-weight: 600; padding: 16px 18px; background: var(--anki-surface); border-left: 3px solid var(--anki-accent); border-radius: 8px; }'
        '.anki-answer-zh { margin-left: 12px; color: var(--anki-fg); font-weight: 700; }'
        '.anki-answer-sub { font-size: 14px; line-height: 1.7; color: var(--anki-muted); }'
        '.anki-support { display: flex; flex-direction: column; gap: 22px; padding-top: 20px; }'
        '.anki-support-block { display: flex; flex-direction: column; gap: 8px; padding: 16px 18px; border: 1px solid var(--anki-border); background: var(--anki-surface); border-radius: 10px; }'
        '.anki-support-title { width: 100%; text-align: left; align-self: flex-start; font-size: 16px; line-height: 1.4; font-weight: 700; color: var(--anki-accent); }'
        '.anki-support-text { font-size: 16px; line-height: 1.75; color: var(--anki-muted); }'
        '.anki-support-zh { font-size: 15px; line-height: 1.75; color: var(--anki-fg); }'
        '.anki-support-zh-inline { margin-left: 12px; color: var(--anki-fg); font-size: 15px; font-weight: 400; }'
        '.anki-support-text strong, .anki-extension-item strong, .anki-example-en strong { color: var(--anki-fg); font-weight: 700; }'
        '.anki-support-zh strong, .anki-support-zh-inline strong, .anki-example-zh strong { color: var(--anki-fg); font-weight: 700; }'
        '.anki-extension-item { font-size: 15px; line-height: 1.7; color: var(--anki-fg); }'
        '.anki-extension-item + .anki-extension-item { margin-top: 5px; }'
        '.anki-extension-label { margin-top: 5px; font-size: 14px; line-height: 1.5; font-weight: 700; color: var(--anki-accent); }'
        '.anki-relation-label { margin-top: 5px; font-size: 14px; line-height: 1.5; font-weight: 700; }'
        '.anki-relation-label--synonym, .anki-relation-item--synonym { color: #3d806d; }'
        '.anki-relation-label--antonym, .anki-relation-item--antonym { color: var(--anki-accent); }'
        '.anki-example-en, .anki-example-zh { display: inline; }'
        '.anki-example-zh { margin-left: 10px; color: var(--anki-fg); }'
        '.anki-example-zh strong { color: var(--anki-fg); font-weight: 700; }'
        '.anki-example-source { display: block; margin-top: 2px; color: var(--anki-muted); font-size: 12px; line-height: 1.35; }'
        '.anki-other-meaning { margin-left: 8px; color: var(--anki-fg); font-weight: 700; }'
        '.anki-dictionary-word { font-size: 20px; line-height: 1.5; color: var(--anki-fg); font-weight: 400; }'
        '.anki-dictionary-headline { font-size: 20px; line-height: 1.5; color: var(--anki-fg); font-weight: 400; }'
        '.anki-dictionary-definition { margin-left: 10px; color: var(--anki-fg); font-weight: 700; }'
        '.anki-dictionary-meta-inline { margin-left: 12px; color: var(--anki-muted); font-size: 17px; }'
        '.anki-headword { margin-right: 10px; font-weight: 700; }'
        '.anki-part-of-speech { font-weight: 400; }'
        '.anki-dictionary-meta { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; font-size: 17px; color: var(--anki-muted); }'
        '.anki-audio-button { width: 30px; height: 30px; padding: 0; border: 1px solid var(--anki-border); border-radius: 50%; background: var(--anki-surface); color: var(--anki-accent); font: inherit; font-size: 13px; line-height: 28px; text-align: center; cursor: pointer; }'
        '.anki-audio-button:active { transform: scale(0.94); }'
        '.anki-audio-control { display: none; }'
        '.anki-answer-audio { margin-left: 8px; vertical-align: middle; }'
        '.anki-auto { display: flex; flex-direction: column; gap: 10px; padding: 14px 16px; border-left: 3px solid var(--anki-accent, #3b82f6); background: var(--anki-surface-2, #f8fafc); border-radius: 8px; }'
        '.anki-auto-title { font-size: 14px; font-weight: 700; color: var(--anki-fg); }'
        '.anki-auto-group { display: flex; flex-wrap: wrap; align-items: baseline; gap: 7px; font-size: 14px; line-height: 1.6; }'
        '.anki-label { color: var(--anki-accent, #2563eb); font-weight: 700; }'
        '.anki-chip { display: inline-block; padding: 2px 8px; border: 1px solid var(--anki-border); border-radius: 999px; color: var(--anki-fg); }'
        '.anki-auto-example { font-size: 14px; line-height: 1.7; color: var(--anki-muted); }'
        '.anki-meta { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 4px; color: var(--anki-muted); font-size: 12px; }'
        '.anki-mnemonic-img { margin-top: 8px; text-align: center; }'
        '.anki-card-container img { max-width: 100%; height: auto; }'
        '@media (max-width: 600px) {'
        '  .anki-card-container { max-width: 100%; margin: 0; padding: 16px 14px; border-radius: 10px; }'
        '  .anki-shell { gap: 12px; }'
        '  .anki-question { font-size: 18px; line-height: 1.42; padding-bottom: 14px; }'
        '  .anki-choice-options { gap: 8px; margin-top: 13px; }'
        '  .anki-choice-option { gap: 8px; padding: 10px 11px; font-size: 15px; }'
        '  .anki-choice-submit { padding: 9px 14px; font-size: 14px; }'
        '  .anki-choice-feedback { font-size: 13px; }'
        '  .anki-vocab-type { font-size: 14px; }'
        '  .anki-vocab-sentence { padding: 12px 0 14px; font-size: 19px; line-height: 1.42; }'
        '  .anki-answer { gap: 5px; }'
        '  .anki-answer-title { font-size: 14px; }'
        '  .anki-answer-main { font-size: 17px; line-height: 1.42; padding: 11px 12px; }'
        '  .anki-answer-zh { margin-left: 7px; }'
        '  .anki-support { gap: 14px; padding-top: 12px; }'
        '  .anki-support-block { gap: 5px; padding: 11px 12px; border-radius: 8px; }'
        '  .anki-support-title { font-size: 14px; }'
        '  .anki-support-text { font-size: 14px; line-height: 1.5; }'
        '  .anki-support-zh, .anki-support-zh-inline { font-size: 13px; line-height: 1.5; }'
        '  .anki-dictionary-headline { font-size: 17px; line-height: 1.45; }'
        '  .anki-dictionary-meta-inline { margin-left: 7px; font-size: 14px; }'
        '  .anki-dictionary-definition { margin-left: 6px; }'
        '  .anki-dictionary-meta { font-size: 14px; }'
        '  .anki-extension-item { font-size: 13px; line-height: 1.45; }'
        '  .anki-relation-label, .anki-extension-label { font-size: 13px; line-height: 1.4; }'
        '  .anki-example-zh { margin-left: 7px; }'
        '  .anki-other-meaning { margin-left: 5px; }'
        '  .anki-audio-button { width: 26px; height: 26px; line-height: 24px; font-size: 11px; }'
        '}'
        '.mobile .anki-extension-block, body.mobile .anki-extension-block { padding: 8px 9px; gap: 3px; }'
        '.mobile .anki-extension-block .anki-support-title, body.mobile .anki-extension-block .anki-support-title { font-size: 13px; line-height: 1.3; }'
        '.mobile .anki-extension-block .anki-extension-item, body.mobile .anki-extension-block .anki-extension-item { font-size: 11.5px; line-height: 1.3; }'
        '.mobile .anki-extension-block .anki-relation-label, body.mobile .anki-extension-block .anki-relation-label { font-size: 14px; line-height: 1.45; }'
        '.mobile .anki-extension-block .anki-relation-items, body.mobile .anki-extension-block .anki-relation-items { text-align: left; font-size: 14px; line-height: 1.45; }'
        '.mobile .anki-extension-block .anki-relation-item, body.mobile .anki-extension-block .anki-relation-item { font-size: inherit; }'
        '.mobile .anki-extension-block .anki-other-meaning, body.mobile .anki-extension-block .anki-other-meaning { margin-left: 4px; }'
        '.mobile .anki-extension-block .anki-example-en, .mobile .anki-extension-block .anki-example-zh, body.mobile .anki-extension-block .anki-example-en, body.mobile .anki-extension-block .anki-example-zh { font-size: 12px; line-height: 1.35; }'
        '.nightMode .anki-card-container, body.nightMode .anki-card-container, .night_mode .anki-card-container, body.night_mode .anki-card-container { '
        '  --anki-bg: #171717; '
        '  --anki-surface: #202020; '
        '  --anki-fg: #eeeeeb; '
        '  --anki-muted: #b4b0aa; '
        '  --anki-border: #41403d; '
        '  --anki-surface-2: #1b1b1b; '
        '  --anki-accent: #d18478; '
        '}'
        '@media (prefers-color-scheme: dark) {'
        '  .anki-card-container { '
        '    --anki-bg: #171717; '
        '    --anki-surface: #202020; '
        '    --anki-fg: #eeeeeb; '
        '    --anki-muted: #b4b0aa; '
        '    --anki-border: #41403d; '
        '    --anki-surface-2: #1b1b1b; '
        '    --anki-accent: #d18478; '
        '  }'
        '}'
        '</style>'
    )


def get_source_summary(source):
    if not isinstance(source, dict):
        return ""

    pieces = []
    for key in ("title", "chapter", "file", "page"):
        value = source.get(key)
        if value:
            pieces.append(str(value))
    return " · ".join(pieces)


def estimate_load(card):
    score = 0
    front = card.get("front", "") or ""
    explanation = card.get("explanation", "") or ""
    mnemonic = card.get("mnemonic_hook", "") or ""
    options = card.get("options", []) or []

    score += min(len(front) // 80, 2)
    score += min(len(explanation) // 120, 2)
    score += min(len(mnemonic) // 80, 1)
    score += 1 if len(options) >= 4 else 0

    if score <= 1:
        return "轻量"
    if score <= 3:
        return "标准"
    return "密集"


def count_cloze_deletions(front):
    if not isinstance(front, str):
        return 0
    return front.count("{{c")


def render_badge(text, kind=""):
    kind_class = f" anki-badge--{kind}" if kind else ""
    return f'<span class="anki-badge{kind_class}">{format_multiline_text(text)}</span>'


def render_chip(text, kind=""):
    kind_class = f" anki-chip--{kind}" if kind else ""
    return f'<span class="anki-chip{kind_class}">{format_multiline_text(text)}</span>'


def contains_cjk(text):
    return bool(re.search(r"[\u4e00-\u9fff]", "" if text is None else str(text)))


def should_show_secondary(primary, secondary):
    primary_text = "" if primary is None else str(primary)
    secondary_text = "" if secondary is None else str(secondary)
    if not secondary_text.strip():
        return False
    if re.sub(r"\s+", "", primary_text) == re.sub(r"\s+", "", secondary_text):
        return False
    if contains_cjk(primary_text) and contains_cjk(secondary_text):
        return False
    return True


def normalize_text_items(value):
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]

    normalized = []
    seen = set()
    for item in values:
        text = str(item).strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def extract_quoted_terms(text):
    if not isinstance(text, str) or not text:
        return []

    pattern = re.compile(r"'([^']{2,80})'|\"([^\"]{2,80})\"|“([^”]{2,80})”|‘([^’]{2,80})’")
    terms = []
    seen = set()
    for match in pattern.finditer(text):
        term = next(group for group in match.groups() if group)
        candidate = term.strip()
        if candidate and candidate.lower() not in seen:
            terms.append(candidate)
            seen.add(candidate.lower())
    return terms


def extract_cloze_terms(text):
    if not isinstance(text, str) or not text:
        return []

    pattern = re.compile(r"\{\{c\d+::(.*?)(?:::.*?)?\}\}")
    terms = []
    seen = set()
    for match in pattern.finditer(text):
        candidate = match.group(1).strip()
        if candidate and candidate.lower() not in seen:
            terms.append(candidate)
            seen.add(candidate.lower())
    return terms


def strip_cloze_markup(text):
    if not isinstance(text, str) or not text:
        return ""

    def repl(match):
        return match.group(1).split("::", 1)[0].strip()

    return re.sub(r"\{\{c\d+::(.*?)(?:::.*?)?\}\}", repl, text)


def token_candidates(text):
    if not isinstance(text, str) or not text:
        return []

    english_stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "how",
        "if",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "to",
        "through",
        "via",
        "was",
        "we",
        "what",
        "when",
        "which",
        "who",
        "why",
        "with",
        "this",
        "those",
        "these",
        "into",
        "over",
        "under",
        "best",
        "rare",
        "meaning",
        "sentence",
        "following",
        "question",
        "answer",
        "explanation",
        "production",
        "generate",
        "something",
        "very",
        "carefully",
        "detail",
        "details",
        "years",
        "private",
        "privately",
        "less",
        "make",
        "severe",
        "harmful",
        "means",
        "means",
        "means",
    }
    chinese_stopwords = {
        "这里",
        "这个",
        "那个",
        "通常",
        "表示",
        "可以",
        "或者",
        "并且",
        "以及",
        "不是",
        "不同",
        "长期",
        "怀有",
        "某种",
        "一种",
        "这个意思",
        "这里的",
        "作动词",
        "作名词",
        "用来",
        "通过",
        "由于",
        "因为",
        "表示",
        "意思",
    }
    chinese_noise_markers = ("可以", "或者", "并由", "并需", "并且", "以及")
    pattern = re.compile(r"[A-Za-z][A-Za-z'-]{2,}|[\u4e00-\u9fff]{2,8}")
    candidates = []
    seen = set()
    for raw in pattern.findall(text):
        token = raw.strip(" ,.;:!?()[]{}\"'")
        if not token:
            continue
        lower = token.lower()
        if lower in english_stopwords or token in chinese_stopwords:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{2,8}", token):
            if token.startswith(("由", "并", "可", "或")):
                continue
            if any(marker in token for marker in chinese_noise_markers):
                continue
        if len(token) <= 2 and not re.fullmatch(r"[\u4e00-\u9fff]{2,}", token):
            continue
        if lower not in seen:
            candidates.append(token)
            seen.add(lower)
    return candidates


def resolve_choice_answer(card):
    answer = card.get("correct_answer", "")
    options = card.get("options", []) or []
    if isinstance(answer, str) and len(answer) == 1 and answer.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        idx = ord(answer.upper()) - 65
        if 0 <= idx < len(options):
            return options[idx]
    if isinstance(answer, str):
        normalized = answer.upper().strip()
        if re.fullmatch(r"[A-Z](?:\s*[,/&]\s*[A-Z])+|[A-Z]{2,}", normalized):
            letters = re.findall(r"[A-Z]", normalized)
            resolved = []
            for letter in letters:
                idx = ord(letter) - 65
                if idx >= len(options):
                    return answer
                resolved.append(f"{letter}. {options[idx]}")
            return "; ".join(resolved)
    return answer


def extract_dictionary_word(card):
    explicit = str(card.get("word", "") or "").strip()
    if explicit:
        return explicit
    front = card.get("front", "") or ""
    cloze_terms = extract_cloze_terms(front)
    if cloze_terms:
        return cloze_terms[0]
    quoted_terms = extract_quoted_terms(front)
    for term in quoted_terms:
        if re.fullmatch(r"[A-Za-z][A-Za-z'-]*", term.strip()):
            return term.strip()
    return ""


def is_vocabulary_card(card):
    card_type = normalize_card_type(card.get("type", "QA"))
    if infer_question_type(card) == "vocabulary_meaning":
        return True
    word = extract_dictionary_word(card)
    if not word:
        return False
    if card_type == "Cloze":
        return bool(re.search(r"[A-Za-z]", word)) and not contains_cjk(word)
    if card.get("word"):
        return True
    tags = " ".join(normalize_text_items(card.get("tags"))).lower()
    text = " ".join(str(card.get(key, "") or "") for key in ("front", "back", "explanation")).lower()
    return any(marker in f"{tags} {text}" for marker in ("vocabulary", "ielts", "english", "polysemy", "熟词僻义", "词汇"))


def render_extension_block(title, values):
    items = normalize_text_items(values)
    if not items:
        return ""
    body = "".join(f'<div class="anki-extension-item">{format_multiline_text(item)}</div>' for item in items)
    return f'<div class="anki-support-block anki-extension-block"><div class="anki-support-title">{escape_text(title)}</div>{body}</div>'


def render_extension_group(title, sections):
    populated = [(label, normalize_text_items(values)) for label, values in sections]
    populated = [(label, values) for label, values in populated if values]
    if not populated:
        return ""
    parts = [f'<div class="anki-support-block anki-extension-block"><div class="anki-support-title">{escape_text(title)}</div>']
    for label, values in populated:
        parts.append(f'<div class="anki-extension-label">{escape_text(label)}</div>')
        parts.extend(f'<div class="anki-extension-item">{format_multiline_text(item)}</div>' for item in values)
    parts.append('</div>')
    return "".join(parts)


def render_relation_block(card, root_items, near_synonyms, confusable_words, collocations):
    sections = [
        ("同义词", card.get("synonyms"), "synonym"),
        ("反义词", card.get("antonyms"), "antonym"),
        ("近义词", near_synonyms, "neutral"),
        ("形近词 / 易混词", confusable_words, "neutral"),
        ("固定搭配", collocations, "neutral"),
        ("词根词缀", root_items, "neutral"),
    ]
    populated = [(label, normalize_text_items(values), kind) for label, values, kind in sections]
    populated = [(label, values, kind) for label, values, kind in populated if values]
    if not populated:
        return ""
    parts = ['<div class="anki-support-block anki-extension-block"><div class="anki-support-title">词汇关系</div>']
    for label, values, kind in populated:
        label_class = f" anki-relation-label--{kind}" if kind != "neutral" else ""
        item_class = f" anki-relation-item--{kind}" if kind != "neutral" else ""
        inline_items = "; ".join(
            f'<span class="anki-extension-item anki-relation-item{item_class}">{format_multiline_text(item)}</span>'
            for item in values
        )
        parts.append(f'<div class="anki-relation-items"><span class="anki-relation-label{label_class}">{escape_text(label)}</span>　{inline_items}</div>')
    parts.append('</div>')
    return "".join(parts)


def bold_target_text(text, target):
    rendered = format_multiline_text(text)
    safe_target = escape_text(target)
    if not safe_target:
        return rendered
    return re.sub(re.escape(safe_target), f"<strong>{safe_target}</strong>", rendered, flags=re.IGNORECASE)


def extract_vocabulary_sentence(card):
    if normalize_card_type(card.get("type", "QA")) != "QA":
        return ""
    front = str(card.get("front", "") or "").strip()
    patterns = (
        r"^What is the definition of ['\u2018\u2019\"]([^'\u2018\u2019\"]+)['\u2018\u2019\"] in the (?:phrase|sentence) ['\u2018\u2019\"](.+?)['\u2018\u2019\"]\??$",
        r"^What is the rare meaning of ['\u2018\u2019\"]([^'\u2018\u2019\"]+)['\u2018\u2019\"] in the sentence ['\u2018\u2019\"](.+?)['\u2018\u2019\"]\??$",
    )
    for pattern in patterns:
        match = re.match(pattern, front, flags=re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return ""


def question_type_label(card):
    question_type = infer_question_type(card)
    if question_type == "cloze":
        return "填空题"
    if question_type == "vocabulary_meaning":
        return "词义题"
    if question_type == "multiple_choice":
        return "多选题"
    if question_type == "single_choice":
        return "单选题"
    if question_type == "true_false":
        return "判断题"
    return "简答题"


def guess_word_kind(target, card):
    text = " ".join(
        str(card.get(key, "") or "")
        for key in ("front", "back", "explanation", "back_zh", "explanation_zh")
    ).lower()
    if isinstance(target, str):
        lower = target.lower()
        if f"{lower} means to" in text or "作动词" in text or "表示" in text and "情绪" in text:
            return "verb"
        if f"{lower} means" in text or "a monetary penalty" in text or "罚款" in text or "处罚" in text:
            return "noun"
        if "synonym for" in text or "同义" in text or "近义" in text:
            return "word"
    return "word"


def extract_core_keywords(card):
    explicit = normalize_text_items(card.get("core_keywords"))
    if explicit:
        return explicit[:4]

    candidates = []
    card_type = normalize_card_type(card.get("type", "QA"))
    front = card.get("front", "") or ""
    text_blob = " ".join(
        str(card.get(key, "") or "")
        for key in ("front", "back", "explanation", "back_zh", "explanation_zh")
    )

    phrase_hints = (
        "全国人大常委会",
        "全国人大代表",
        "全国人民代表大会",
        "宪法修改",
        "五分之一以上",
        "三分之二以上",
        "主席团",
    )
    for phrase in phrase_hints:
        if phrase in text_blob:
            candidates.append(phrase)

    if card_type == "Cloze":
        candidates.extend(extract_cloze_terms(front))
        candidates.extend(extract_quoted_terms(front))
    else:
        for term in extract_quoted_terms(front):
            if len(term.split()) <= 4:
                candidates.append(term)
        candidates.extend(extract_cloze_terms(front))

    for key in ("back", "explanation", "back_zh", "explanation_zh"):
        candidates.extend(token_candidates(card.get(key, "") or ""))

    seen = set()
    result = []
    for candidate in candidates:
        token = str(candidate).strip()
        if not token:
            continue
        lower = token.lower()
        if lower in seen:
            continue
        seen.add(lower)
        result.append(token)
        if len(result) >= 4:
            break
    return result


def extract_related_terms(card):
    synonyms = normalize_text_items(card.get("synonyms"))
    antonyms = normalize_text_items(card.get("antonyms"))
    contrast = normalize_text_items(card.get("contrast_terms"))

    if synonyms or antonyms or contrast:
        return {"synonyms": synonyms, "antonyms": antonyms, "contrast": contrast}

    front = card.get("front", "") or ""
    front_lower = front.lower()
    target_terms = extract_core_keywords(card)
    answer_text = resolve_choice_answer(card) if normalize_card_type(card.get("type", "QA")) == "Choice" else ""

    if any(marker in front_lower for marker in ("synonym", "同义", "近义")) and answer_text:
        synonyms = [answer_text]
    elif any(marker in front_lower for marker in ("antonym", "opposite", "反义")) and answer_text:
        antonyms = [answer_text]

    contrast_patterns = [
        r"different meaning from ['\"“‘]([^'\"”’]+)['\"”’]\s+meaning\s+([^.，。]+)",
        r"different meaning from ['\"“‘]([^'\"”’]+)['\"”’]",
        r"different from ['\"“‘]([^'\"”’]+)['\"”’]",
        r"not ['\"“‘]([^'\"”’]+)['\"”’]",
    ]
    source_text = " ".join(
        str(card.get(key, "") or "")
        for key in ("back", "explanation", "back_zh", "explanation_zh")
    )
    for pattern in contrast_patterns:
        match = re.search(pattern, source_text, flags=re.IGNORECASE)
        if match:
            contrast = [match.group(2).strip() if match.lastindex and match.lastindex >= 2 and match.group(2) else match.group(1).strip()]
            break

    if not (synonyms or antonyms or contrast):
        if target_terms and answer_text and normalize_card_type(card.get("type", "QA")) == "Choice":
            if any(marker in front_lower for marker in ("synonym", "同义", "近义")):
                synonyms = [answer_text]
            elif any(marker in front_lower for marker in ("antonym", "opposite", "反义")):
                antonyms = [answer_text]

    return {"synonyms": synonyms, "antonyms": antonyms, "contrast": contrast}


def extract_example_sentence(card):
    explicit = card.get("example_sentence")
    explicit_zh = card.get("example_sentence_zh")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip(), explicit_zh.strip() if isinstance(explicit_zh, str) and explicit_zh.strip() else ""

    front = card.get("front", "") or ""
    card_type = normalize_card_type(card.get("type", "QA"))
    sentences = []

    quoted = extract_quoted_terms(front)
    for candidate in quoted:
        if " " in candidate or re.search(r"[\u4e00-\u9fff]", candidate):
            sentences.append(candidate.strip())

    if card_type == "Cloze":
        stripped = strip_cloze_markup(front).strip()
        if stripped and stripped not in sentences:
            sentences.insert(0, stripped)

    tags = " ".join(normalize_text_items(card.get("tags"))).lower()
    vocab_signals = any(
        marker in " ".join(
            str(card.get(key, "") or "")
            for key in ("front", "back", "explanation", "back_zh", "explanation_zh")
        ).lower()
        for marker in (
            "synonym",
            "antonym",
            "opposite",
            "meaning of",
            "means to",
            "different meaning",
            "rare meaning",
            "同义",
            "反义",
            "近义",
            "熟词僻义",
            "词汇",
            "vocabulary",
            "ielts",
            "english",
        )
    ) or any(marker in tags for marker in ("vocabulary", "ielts", "english", "polysemy", "熟词僻义"))

    target_terms = extract_core_keywords(card)
    target = target_terms[0] if target_terms else ""
    text_blob = " ".join(
        str(card.get(key, "") or "")
        for key in ("front", "back", "explanation", "back_zh", "explanation_zh")
    ).lower()

    if not sentences and target:
        if not vocab_signals:
            return "", ""
        lower_target = target.lower()
        if lower_target == "harbor" and "feeling" in text_blob:
            sentences.append("She harbored resentment for years.")
        elif lower_target == "mitigate":
            sentences.append("The new rules should mitigate the risk.")
        elif lower_target == "scrutinize":
            sentences.append("The committee will scrutinize the proposal before approval.")
        elif lower_target == "fine":
            sentences.append("The court imposed a fine.")
        else:
            kind = guess_word_kind(target, card)
            if kind == "verb":
                sentences.append(f"The committee decided to {target} the proposal.")
            elif kind == "noun":
                article = "an" if target[:1].lower() in "aeiou" else "a"
                sentences.append(f"The court imposed {article} {target}.")
            else:
                sentences.append(f"The student tried to use {target} in a sentence.")

    sentence = sentences[0].strip() if sentences else ""
    if sentence and re.search(r"[A-Za-z]", sentence) and " " in sentence and sentence[-1] not in ".!?":
        sentence = f"{sentence}."
    if sentence and sentence != front.strip():
        return sentence, explicit_zh.strip() if isinstance(explicit_zh, str) and explicit_zh.strip() else ""
    return "", ""


def render_auto_group(label, values, kind="muted"):
    items = normalize_text_items(values)
    if not items:
        return ""
    chips = "".join(render_chip(item, kind) for item in items)
    return (
        '<div class="anki-auto-group">'
        f'<span class="anki-label">{escape_text(label)}：</span>'
        f"{chips}"
        "</div>"
    )


def store_media_file(local_path, anki_urls):
    if not os.path.exists(local_path):
        print(f"Warning: Media file not found at local path '{local_path}'", file=sys.stderr)
        return None

    filename = os.path.basename(local_path)
    with open(local_path, "rb") as f:
        file_bytes = f.read()

    digest = hashlib.sha1(file_bytes).hexdigest()[:12]
    unique_name = f"{digest}_{filename}"
    base64_data = base64.b64encode(file_bytes).decode("utf-8")

    print(f"Uploading media: {unique_name}")
    return request("storeMediaFile", anki_urls=anki_urls, filename=unique_name, data=base64_data)


def generate_word_audio(word):
    """Create a compact English pronunciation file using the macOS speech engine."""
    clean_word = str(word or "").strip()
    if not clean_word:
        return None
    digest = hashlib.sha1(clean_word.lower().encode("utf-8")).hexdigest()[:12]
    aiff_path = os.path.join("/private/tmp", f"anki_word_{digest}.aiff")
    mp3_path = os.path.join("/private/tmp", f"anki_word_{digest}.mp3")
    try:
        subprocess.run(["say", "-v", "Samantha", "-o", aiff_path, clean_word], check=True, timeout=10)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", aiff_path, "-codec:a", "libmp3lame", "-q:a", "4", mp3_path],
            check=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Warning: Could not generate pronunciation for '{clean_word}': {exc}", file=sys.stderr)
        return None
    return mp3_path if os.path.exists(mp3_path) else None


def format_links_and_images(card, media_mapping, include_mathjax=True):
    """
    Format image references and construct a minimal card layout.
    """
    card_type = normalize_card_type(card.get("type", "QA"))

    img_html = ""
    local_img = card.get("mnemonic_image_path")
    if local_img and local_img in media_mapping:
        anki_filename = media_mapping[local_img]
        img_html = (
            '<div class="anki-mnemonic-img" style="margin-top: 15px; text-align: center;">'
            f'<img src="{anki_filename}" style="max-width: 100%; border-radius: 8px; border: 1px solid #ddd;">'
            "</div>"
        )

    mnemonic_text = (card.get("mnemonic_hook", "") or "").strip()
    mnemonic_text_zh = (card.get("mnemonic_hook_zh", "") or "").strip()
    explanation = (card.get("explanation", "") or "").strip()
    explanation_zh = (card.get("explanation_zh", "") or "").strip()
    back_zh = (card.get("back_zh", "") or "").strip()
    explanation_target_zh = (card.get("explanation_target_zh", "") or "").strip()
    mnemonic_target_zh = (card.get("mnemonic_target_zh", "") or "").strip()
    part_of_speech = (card.get("part_of_speech", "") or "").strip()
    phonetic = (card.get("phonetic", "") or "").strip()
    definition_zh = (card.get("definition_zh", "") or "").strip()
    word_level = (card.get("word_level", "") or "").strip()
    oxford_definition = (card.get("oxford_definition", "") or "").strip()
    collins_definition = (card.get("collins_definition", "") or "").strip()
    oxford_definition_zh = (card.get("oxford_definition_zh", "") or "").strip()
    collins_definition_zh = (card.get("collins_definition_zh", "") or "").strip()
    near_synonyms = card.get("near_synonyms")
    confusable_words = card.get("confusable_words")
    collocations = card.get("collocations")
    word_root = (card.get("word_root", "") or "").strip()
    word_affixes = (card.get("word_affixes", "") or "").strip()
    example_sentences = normalize_text_items(card.get("example_sentences"))
    example_sentences_zh = normalize_text_items(card.get("example_sentences_zh"))
    example_sources = normalize_text_items(card.get("example_sources"))
    raw_example_targets_zh = card.get("example_targets_zh") or []
    example_targets_zh = [str(item).strip() for item in raw_example_targets_zh if str(item).strip()] if isinstance(raw_example_targets_zh, (list, tuple)) else []
    other_meanings = card.get("other_meanings")
    other_meanings_examples = normalize_text_items(card.get("other_meanings_examples"))
    core_keywords = extract_core_keywords(card)
    related_terms = extract_related_terms(card)
    example_sentence, example_sentence_zh = extract_example_sentence(card)
    source_summary = get_source_summary(card.get("source"))
    tags = normalize_text_items(card.get("tags"))
    chinese_qa = card_type == "QA" and contains_cjk(card.get("front", "")) and not is_vocabulary_card(card)
    meaning_question = infer_question_type(card) == "vocabulary_meaning" and bool(extract_vocabulary_sentence(card))
    vocabulary_cloze = card_type == "Cloze" and is_vocabulary_card(card)
    compact_vocabulary_card = meaning_question or vocabulary_cloze

    def build_audio_control_html(word):
        audio_filename = media_mapping.get(f"__audio__:{str(word or '').lower()}") if word else None
        if not audio_filename:
            return ""
        audio_src = escape_text(audio_filename)
        return (
            '<span class="anki-audio-wrap anki-answer-audio">'
            '<button type="button" class="anki-audio-button" aria-label="播放读音" '
            'onclick="event.stopPropagation();var a=this.nextElementSibling;a.currentTime=0;a.play();return false;">▶</button>'
            f'<audio class="anki-audio-control" preload="none" src="{audio_src}"></audio>'
            '</span>'
        )

    def append_answer_audio(answer_content):
        if chinese_qa or not is_vocabulary_card(card):
            return answer_content
        return answer_content + build_audio_control_html(extract_dictionary_word(card))

    style_block = build_style_block()
    mathjax_block = build_mathjax_block() if include_mathjax else ""

    def build_answer_html():
        if meaning_question:
            word = extract_dictionary_word(card)
            word_html = f'<span class="anki-headword">{format_multiline_text(word)}</span>' if word else ""
            pos_html = f'<span class="anki-part-of-speech">{format_multiline_text(part_of_speech)}</span>' if part_of_speech else ""
            definition_html = f'<span class="anki-dictionary-definition">{format_multiline_text(definition_zh)}</span>' if definition_zh else ""
            headline = " ".join(item for item in (word_html, pos_html) if item) + definition_html
            meta_parts = [item for item in (word_level, phonetic) if item]
            audio_html = build_audio_control_html(word)
            if audio_html:
                meta_parts.append(audio_html)
            if meta_parts:
                headline += '<span class="anki-dictionary-meta-inline">' + ' • '.join(meta_parts) + '</span>'
            return f'<div class="anki-answer"><div class="anki-answer-title">Answer</div><div class="anki-answer-main">{headline}</div></div>'
        answer_title = "答案" if chinese_qa else ("Correct answer" if card_type == "Choice" else "Answer")
        if card_type == "Choice":
            answer_text = choice_answer_display(card)
            answer_content = format_multiline_text(answer_text)
            if should_show_secondary(answer_text, back_zh):
                answer_content += f'<span class="anki-answer-zh">{format_multiline_text(back_zh)}</span>'
            answer_content = append_answer_audio(answer_content)
            return f'<div class="anki-answer"><div class="anki-answer-title">{answer_title}</div><div class="anki-answer-main">{answer_content}</div></div>'

        if card_type == "QA":
            answer_text = ((card.get("back_zh", "") if chinese_qa else card.get("back", "")) or "").strip()
            answer_content = format_multiline_text(answer_text)
            if not chinese_qa and should_show_secondary(answer_text, back_zh):
                answer_content += f'<span class="anki-answer-zh">{format_multiline_text(back_zh)}</span>'
            answer_content = append_answer_audio(answer_content)
            return f'<div class="anki-answer"><div class="anki-answer-title">{answer_title}</div><div class="anki-answer-main">{answer_content}</div></div>'

        if card_type == "Cloze":
            answer_text = (card.get("back", "") or "").strip()
            if not answer_text:
                deleted_terms = extract_cloze_terms(card.get("front", "") or "")
                answer_text = ", ".join(deleted_terms) or strip_cloze_markup(card.get("front", "") or "").strip()
            if not answer_text:
                return ""
            answer_content = format_multiline_text(answer_text)
            if should_show_secondary(answer_text, back_zh):
                answer_content += f'<span class="anki-answer-zh">{format_multiline_text(back_zh)}</span>'
            answer_content = append_answer_audio(answer_content)
            return f'<div class="anki-answer"><div class="anki-answer-title">{answer_title}</div><div class="anki-answer-main">{answer_content}</div></div>'

        return ""

    def build_explanation_html():
        if compact_vocabulary_card:
            return ""
        if not (explanation or explanation_zh):
            return ""

        expl_parts = ['<div class="anki-support-block">', '<div class="anki-support-title">解读</div>']
        if chinese_qa and explanation_zh:
            expl_parts.append(f'<div class="anki-support-zh">{format_multiline_text(explanation_zh)}</div>')
        elif explanation:
            expl_parts.append(f'<div class="anki-support-text">{bold_target_text(explanation, extract_dictionary_word(card))}</div>')
        if not chinese_qa and should_show_secondary(explanation, explanation_zh):
            expl_parts.append(f'<div class="anki-support-zh">{bold_target_text(explanation_zh, explanation_target_zh)}</div>')
        expl_parts.append('</div>')
        return "".join(expl_parts)

    def build_memory_html():
        if compact_vocabulary_card:
            return ""
        if not (mnemonic_text or mnemonic_text_zh or img_html):
            return ""

        memory_parts = ['<div class="anki-support-block">', '<div class="anki-support-title">口诀</div>']
        if chinese_qa and mnemonic_text_zh:
            memory_parts.append(f'<div class="anki-support-zh">{format_multiline_text(mnemonic_text_zh)}</div>')
        elif mnemonic_text:
            mnemonic_content = bold_target_text(mnemonic_text, extract_dictionary_word(card))
            if not chinese_qa and should_show_secondary(mnemonic_text, mnemonic_text_zh):
                mnemonic_content += f'<span class="anki-support-zh-inline">{bold_target_text(mnemonic_text_zh, mnemonic_target_zh)}</span>'
            memory_parts.append(f'<div class="anki-support-text">{mnemonic_content}</div>')
        if img_html:
            memory_parts.append(img_html)
        memory_parts.append('</div>')
        return "".join(memory_parts)

    def build_dictionary_html():
        values = (part_of_speech, phonetic, definition_zh, word_level, oxford_definition, collins_definition)
        if not any(values):
            return ""
        parts = ['<div class="anki-support-block"><div class="anki-support-title">词典释义</div>']
        if meaning_question:
            if oxford_definition:
                parts.append(f'<div class="anki-support-text"><strong>Oxford:</strong> {format_multiline_text(oxford_definition)}</div>')
                if oxford_definition_zh:
                    parts.append(f'<div class="anki-support-zh">{format_multiline_text(oxford_definition_zh)}</div>')
            if collins_definition:
                parts.append(f'<div class="anki-support-text"><strong>Collins:</strong> {format_multiline_text(collins_definition)}</div>')
                if collins_definition_zh:
                    parts.append(f'<div class="anki-support-zh">{format_multiline_text(collins_definition_zh)}</div>')
            parts.append('</div>')
            return "".join(parts)
        word = extract_dictionary_word(card)
        word_html = f'<span class="anki-headword">{format_multiline_text(word)}</span>' if word else ""
        pos_html = f'<span class="anki-part-of-speech">{format_multiline_text(part_of_speech)}</span>' if part_of_speech else ""
        word_head = " ".join(item for item in (word_html, pos_html) if item)
        meta_parts = [item for item in (word_level, phonetic) if item]
        audio_html = build_audio_control_html(word)
        if audio_html:
            meta_parts.append(audio_html)
        meta_html = ""
        if meta_parts:
            meta_html = '<span class="anki-dictionary-meta-inline">' + ' • '.join(meta_parts) + '</span>'
        definition_html = f'<span class="anki-dictionary-definition">{format_multiline_text(definition_zh)}</span>' if definition_zh else ""
        if word_head or definition_html or meta_html:
            parts.append(f'<div class="anki-dictionary-headline">{word_head}{definition_html}{meta_html}</div>')
        if oxford_definition:
            parts.append(f'<div class="anki-support-text"><strong>Oxford:</strong> {format_multiline_text(oxford_definition)}</div>')
            if oxford_definition_zh:
                parts.append(f'<div class="anki-support-zh">{format_multiline_text(oxford_definition_zh)}</div>')
        if collins_definition:
            parts.append(f'<div class="anki-support-text"><strong>Collins:</strong> {format_multiline_text(collins_definition)}</div>')
            if collins_definition_zh:
                parts.append(f'<div class="anki-support-zh">{format_multiline_text(collins_definition_zh)}</div>')
        parts.append('</div>')
        return "".join(parts)

    def build_relation_html():
        if not is_vocabulary_card(card):
            return ""
        root_items = []
        if word_root:
            root_items.append(f"词根：{word_root}")
        if word_affixes:
            root_items.append(f"词缀：{word_affixes}")
        return render_relation_block(card, root_items, near_synonyms, confusable_words, collocations)

    def build_examples_html():
        if not is_vocabulary_card(card):
            return ""
        if len(example_sentences) >= 3 and len(example_sentences_zh) >= 3 and len(example_targets_zh) >= 3:
            example_items = []
            for index, (english, chinese, chinese_target) in enumerate(zip(example_sentences[:3], example_sentences_zh[:3], example_targets_zh[:3]), 1):
                source_html = ""
                if index <= len(example_sources):
                    source_html = f'<span class="anki-example-source">出处：{format_multiline_text(example_sources[index - 1])}</span>'
                example_items.append(
                    f'<div class="anki-extension-item">{index}. '
                    f'<span class="anki-example-en">{bold_target_text(english, extract_dictionary_word(card))}</span>'
                    f'<span class="anki-example-zh">{bold_target_text(chinese, chinese_target)}</span>{source_html}</div>'
                )
            return '<div class="anki-support-block anki-extension-block"><div class="anki-support-title">双语例句</div>' + "".join(example_items) + '</div>'
        return ""

    def build_other_meanings_html():
        if not is_vocabulary_card(card):
            return ""
        other_items = normalize_text_items(other_meanings)
        if other_items and len(other_items) == len(other_meanings_examples):
            other_parts = ['<div class="anki-support-block anki-extension-block"><div class="anki-support-title">其他含义</div>']
            for meaning, example in zip(other_items, other_meanings_examples):
                other_parts.append(
                    f'<div class="anki-extension-item">{bold_target_text(example, extract_dictionary_word(card))} '
                    f'<span class="anki-other-meaning">{format_multiline_text(meaning)}</span></div>'
                )
            other_parts.append('</div>')
            return "".join(other_parts)
        return ""

    if card_type == "Choice":
        front_html = render_choice_surface(card, style_block, mathjax_block, "front")
        support_html = "".join(
            (
                build_explanation_html(),
                build_memory_html(),
                build_relation_html(),
            )
        )
        back_html = render_choice_surface(card, style_block, mathjax_block, "back", support_html)
        return front_html, back_html

    def build_auto_html():
        # Automatic helper data remains available to callers, but is intentionally
        # omitted from the card face to keep the study surface focused.
        return ""

    def build_metadata_html():
        return ""

    prompt_parts = [style_block + mathjax_block, '<div class="anki-card-container"><div class="anki-shell">']
    prompt_text = card.get("front", "")
    vocab_sentence = extract_vocabulary_sentence(card) if is_vocabulary_card(card) else ""
    if vocab_sentence:
        prompt_parts.append('<div class="anki-vocab-type">词义题</div>')
        prompt_parts.append(f'<div class="anki-vocab-sentence">{bold_target_text(vocab_sentence, extract_dictionary_word(card))}</div>')
    else:
        prompt_parts.append(f'<div class="anki-vocab-type">{question_type_label(card)}</div>')
        prompt_parts.append(f'<div class="anki-question">{format_multiline_text(prompt_text)}</div>')
    prompt_parts.append('</div></div>')

    answer_parts = [
        style_block + mathjax_block,
        '<div class="anki-card-container"><div class="anki-shell"><div class="anki-support">',
        build_answer_html(),
        build_dictionary_html(),
        build_examples_html(),
        build_explanation_html(),
        build_memory_html(),
        build_relation_html(),
        build_other_meanings_html(),
        '</div></div></div>',
    ]

    return "".join(prompt_parts), "".join(answer_parts)


def sync_cards(
    cards,
    target_deck,
    dry_run=False,
    cloze_extra_field=DEFAULT_CLOZE_EXTRA_FIELD,
    anki_urls=DEFAULT_ANKI_CONNECT_URLS,
):
    validation_errors = validate_cards(cards)

    if validation_errors:
        print("Validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    media_mapping = {}
    for card in cards:
        local_img = card.get("mnemonic_image_path")
        if local_img and local_img not in media_mapping:
            if not dry_run:
                stored_name = store_media_file(local_img, anki_urls)
                if stored_name:
                    media_mapping[local_img] = stored_name
            else:
                print(f"[Dry-Run] Would upload media: {os.path.basename(local_img)}")
                media_mapping[local_img] = os.path.basename(local_img)

        word = extract_dictionary_word(card)
        if word and f"__audio__:{word.lower()}" not in media_mapping:
            if not dry_run:
                audio_path = generate_word_audio(word)
                if audio_path:
                    stored_name = store_media_file(audio_path, anki_urls)
                    if stored_name:
                        media_mapping[f"__audio__:{word.lower()}"] = stored_name
            else:
                print(f"[Dry-Run] Would generate pronunciation: {word}")
                media_mapping[f"__audio__:{word.lower()}"] = f"anki_word_{word.lower()}.mp3"

    notes_payload = []
    for card in cards:
        card_type = normalize_card_type(card.get("type", "QA"))
        tags = normalize_tags(card.get("tags"))

        front_formatted, back_formatted = format_links_and_images(card, media_mapping)

        if card_type == "Cloze":
            model_name = "Cloze"
            fields = {
                "Text": front_formatted,
                cloze_extra_field: back_formatted,
            }
        elif card_type == "Choice":
            model_name = CHOICE_MODEL_NAME
            fields = {
                "Front": front_formatted,
                "Back": back_formatted,
            }
        else:
            model_name = "Basic"
            fields = {
                "Front": front_formatted,
                "Back": back_formatted,
            }

        note = {
            "deckName": target_deck,
            "modelName": model_name,
            "fields": fields,
            "tags": tags,
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
            },
        }
        notes_payload.append(note)

    if dry_run:
        print(f"\n[Dry-Run] Validated {len(notes_payload)} cards ready for deck '{target_deck}':")
        for idx, note in enumerate(notes_payload):
            print(f"  {idx + 1}. Type: {note['modelName']} | Tags: {note['tags']}")
            if note["modelName"] == "Cloze":
                print(f"     Text: {note['fields']['Text'][:100]}...")
                print(f"     Extra field: {cloze_extra_field}")
            else:
                print(f"     Front: {note['fields']['Front'][:100]}...")
        return

    print(f"\nSyncing {len(notes_payload)} cards to deck '{target_deck}'...")
    if any(normalize_card_type(card.get("type", "QA")) == "Choice" for card in cards):
        ensure_choice_model(anki_urls)
    ensure_deck_exists(target_deck, anki_urls)

    results = request("addNotes", anki_urls=anki_urls, notes=notes_payload)

    success_count = sum(1 for r in results if r is not None)
    duplicate_count = sum(1 for r in results if r is None)

    print(f"Sync complete: {success_count} added, {duplicate_count} skipped/duplicates.")


def main():
    parser = argparse.ArgumentParser(description="Sync generated cards to local Anki.")
    parser.add_argument("--file", help="Path to JSON file containing cards.")
    parser.add_argument(
        "--deck",
        default=None,
        help="Target deck name in Anki. Overrides a top-level JSON 'deck' value.",
    )
    parser.add_argument(
        "--anki-url",
        action="append",
        dest="anki_urls",
        help="AnkiConnect URL. Can be passed multiple times to set fallback URLs.",
    )
    parser.add_argument(
        "--cloze-extra-field",
        default=DEFAULT_CLOZE_EXTRA_FIELD,
        help="Field name used for Cloze supplemental content (defaults to Anki's standard Back Extra field).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plans without importing to Anki.")
    args = parser.parse_args()

    deck_from_file = None
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            cards_data = json.load(f)
    else:
        try:
            print("Reading card JSON from stdin...")
            cards_data = json.loads(sys.stdin.read())
        except Exception as e:
            print(f"Error reading JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    if isinstance(cards_data, dict) and isinstance(cards_data.get("cards"), list):
        deck_from_file = cards_data.get("deck")
        cards_data = cards_data["cards"]
    elif not isinstance(cards_data, list):
        if isinstance(cards_data, dict):
            cards_data = [cards_data]
        else:
            print("Error: Input JSON must be a list of card objects", file=sys.stderr)
            sys.exit(1)

    anki_urls = tuple(args.anki_urls) if args.anki_urls else DEFAULT_ANKI_CONNECT_URLS
    target_deck = args.deck or (str(deck_from_file).strip() if deck_from_file else "") or "AnkiCardmaker"
    sync_cards(
        cards_data,
        target_deck,
        dry_run=args.dry_run,
        cloze_extra_field=args.cloze_extra_field,
        anki_urls=anki_urls,
    )


if __name__ == "__main__":
    main()
