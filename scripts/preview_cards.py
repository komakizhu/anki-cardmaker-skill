#!/usr/bin/env python3
import argparse
import html
import os
import shutil
import sys
from pathlib import Path

from anki_sync import extract_dictionary_word, format_links_and_images, generate_word_audio
from card_validation import load_cards, normalize_card_type, normalize_tags, validate_cards


def render_preview(cards, media_mapping=None):
    media_mapping = media_mapping or {}
    rows = []

    for idx, card in enumerate(cards):
        front_html, back_html = format_links_and_images(card, media_mapping)
        card_type = normalize_card_type(card.get("type"))
        tags = ", ".join(normalize_tags(card.get("tags")))
        source = card.get("source", {})
        source_bits = []
        if isinstance(source, dict):
            for key in ("title", "chapter", "file", "url", "page"):
                value = source.get(key)
                if value:
                    source_bits.append(f"{key}: {value}")
        source_text = " | ".join(source_bits) if source_bits else "No source metadata"

        rows.append(
            f"""
            <section class="card">
              <header class="card-header">
                <div>
                  <div class="eyebrow">Card {idx + 1} · {html.escape(card_type)}</div>
                  <h2>{html.escape(str(card.get("front", ""))[:120])}</h2>
                </div>
                <div class="meta">
                  <div><strong>Tags</strong>: {html.escape(tags)}</div>
                  <div><strong>Source</strong>: {html.escape(source_text)}</div>
                </div>
              </header>
              <div class="grid">
                <article>
                  <h3>Front</h3>
                  <div class="panel">{front_html}</div>
                </article>
                <article>
                  <h3>Back</h3>
                  <div class="panel">{back_html}</div>
                </article>
              </div>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Anki Card Preview</title>
  <style>
    :root {{
      color-scheme: light;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      --page-bg: #f4f1ea;
      --page-panel: rgba(255, 253, 248, 0.82);
      --page-border: #e5ddd0;
      --page-ink: #1f2937;
      --page-muted: #6b7280;
      --page-shadow: 0 10px 30px rgba(17, 24, 39, 0.08);
      background:
        radial-gradient(circle at top left, rgba(239, 68, 68, 0.10), transparent 24%),
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.10), transparent 20%),
        linear-gradient(180deg, #fbfaf7, var(--page-bg));
      color: var(--page-ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    body.nightMode, body.night_mode, .nightMode body, .night_mode body {{
      --page-bg: #111827;
      --page-panel: rgba(24, 24, 27, 0.82);
      --page-border: #3f3f46;
      --page-ink: #e5e7eb;
      --page-muted: #a1a1aa;
      --page-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }}
    @media (prefers-color-scheme: dark) {{
      body {{
        --page-bg: #111827;
        --page-panel: rgba(24, 24, 27, 0.82);
        --page-border: #3f3f46;
        --page-ink: #e5e7eb;
        --page-muted: #a1a1aa;
        --page-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      }}
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    .hero {{
      margin-bottom: 28px;
      padding: 24px;
      border: 1px solid var(--border);
      border-radius: 24px;
      background: var(--page-panel);
      box-shadow: var(--page-shadow);
      backdrop-filter: blur(10px);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 40px);
      letter-spacing: -0.03em;
    }}
    .hero p {{
      margin: 0;
      color: var(--page-muted);
      line-height: 1.6;
    }}
    .card {{
      margin-top: 22px;
      padding: 22px;
      border: 1px solid var(--page-border);
      border-radius: 24px;
      background: var(--page-panel);
      box-shadow: var(--page-shadow);
    }}
    .card-header {{
      display: flex;
      gap: 16px;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 18px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--page-border);
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      color: var(--page-muted);
      margin-bottom: 8px;
    }}
    h2 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.35;
    }}
    .meta {{
      min-width: 280px;
      color: var(--page-muted);
      font-size: 14px;
      line-height: 1.5;
      text-align: right;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    article h3 {{
      margin: 0 0 10px;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--page-muted);
    }}
    .panel {{
      min-height: 110px;
      padding: 18px;
      border-radius: 18px;
      border: 1px solid var(--page-border);
      background: var(--page-bg);
      overflow: auto;
    }}
    .panel img {{
      max-width: 100%;
      height: auto;
    }}
    @media (max-width: 900px) {{
      .card-header, .grid {{ grid-template-columns: 1fr; display: grid; }}
      .meta {{ text-align: left; min-width: 0; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Anki Card Preview</h1>
      <p>Generated from the current card payload. Review front and back rendering before syncing to Anki.</p>
    </section>
    {''.join(rows)}
  </div>
</body>
</html>"""


def prepare_preview_media(cards, output_path):
    """Generate local audio files so the standalone preview can play pronunciation."""
    output = Path(output_path).resolve()
    media_dir = output.parent / f"{output.stem}_media"
    media_dir.mkdir(parents=True, exist_ok=True)
    media_mapping = {}
    seen = set()

    for card in cards:
        word = extract_dictionary_word(card)
        key = str(word or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        audio_path = generate_word_audio(word)
        if not audio_path:
            continue
        target = media_dir / Path(audio_path).name
        shutil.copy2(audio_path, target)
        media_mapping[f"__audio__:{key}"] = os.path.relpath(target, output.parent)

    return media_mapping


def main():
    parser = argparse.ArgumentParser(description="Render Anki cards into a standalone HTML preview.")
    parser.add_argument("--file", required=True, help="Path to JSON file containing cards.")
    parser.add_argument("--output", default="preview.html", help="Where to write the HTML preview.")
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

    media_mapping = prepare_preview_media(cards, args.output)
    html_output = render_preview(cards, media_mapping)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Preview written to {args.output}")


if __name__ == "__main__":
    main()
