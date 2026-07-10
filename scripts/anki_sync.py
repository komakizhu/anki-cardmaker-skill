#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import urllib.error
import base64
import argparse

ANKI_CONNECT_URL = "http://localhost:8765"

def request(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANKI_CONNECT_URL, 
        data=data, 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
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
        print(f"Error: Cannot connect to Anki at {ANKI_CONNECT_URL}. Is Anki running with AnkiConnect installed?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"AnkiConnect Error: {e}", file=sys.stderr)
        sys.exit(1)

def ensure_deck_exists(deck_name):
    decks = request("deckNames")
    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found. Creating...")
        request("createDeck", deck=deck_name)

def store_media_file(local_path):
    if not os.path.exists(local_path):
        print(f"Warning: Media file not found at local path '{local_path}'", file=sys.stderr)
        return None
    
    filename = os.path.basename(local_path)
    with open(local_path, "rb") as f:
        file_bytes = f.read()
    
    base64_data = base64.b64encode(file_bytes).decode("utf-8")
    
    print(f"Uploading media: {filename}")
    return request("storeMediaFile", filename=filename, data=base64_data)

def format_links_and_images(card, media_mapping):
    """
    Format image references and construct the card content with mnemonics and source links.
    """
    # Card type: QA, Cloze, Choice
    card_type = card.get("type", "QA")
    
    # Process image if present
    img_html = ""
    local_img = card.get("mnemonic_image_path")
    if local_img and local_img in media_mapping:
        anki_filename = media_mapping[local_img]
        img_html = f'<div class="anki-mnemonic-img" style="margin-top: 15px; text-align: center;"><img src="{anki_filename}" style="max-width: 100%; border-radius: 8px; border: 1px solid #ddd;"></div>'
    
    # Context, hooks
    mnemonic_text = card.get("mnemonic_hook", "")
    explanation = card.get("explanation", "")
    
    # Styling block for sleek looks inside Anki
    style_block = (
        '<style>'
        '.anki-card-container { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }'
        '.anki-explanation { margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; font-size: 14px; color: #555; }'
        '.anki-mnemonic { margin-top: 12px; padding: 10px; background-color: #f6f8fa; border-left: 4px solid #0969da; font-size: 13.5px; border-radius: 4px; }'
        '</style>'
    )
    
    # HTML formatted back/extra content
    back_html = '<div class="anki-card-container">'
    if card_type == "QA":
        back_html += f'<div class="anki-answer">{card.get("back", "")}</div>'
    elif card_type == "Choice":
        back_html += f'<div class="anki-choice-ans" style="font-weight: bold; color: #2da44e; font-size: 18px;">正确答案: {card.get("correct_answer", "")}</div>'
    
    if explanation:
        back_html += f'<div class="anki-explanation"><strong>解析:</strong><br>{explanation}</div>'
        
    if mnemonic_text:
        back_html += f'<div class="anki-mnemonic">💡 <strong>记忆钩子:</strong><br>{mnemonic_text}</div>'
        
    back_html += img_html
    back_html += style_block
    back_html += '</div>'
    
    # Setup front
    front_html = '<div class="anki-card-container">'
    if card_type == "QA":
        front_html += card.get("front", "")
    elif card_type == "Choice":
        # Format Choice question
        front_html += f'<div class="anki-choice-q" style="font-weight: 500; font-size: 16px; margin-bottom: 10px;">{card.get("front", "")}</div>'
        options = card.get("options", [])
        if options:
            front_html += '<ul class="anki-options-list" style="list-style-type: none; padding-left: 0; margin-top: 10px;">'
            for idx, opt in enumerate(options):
                prefix = chr(65 + idx) # A, B, C, D
                front_html += f'<li style="margin-bottom: 8px; padding: 6px 12px; background-color: #fafbfc; border: 1px solid #e1e4e8; border-radius: 6px;"><strong>{prefix}.</strong> {opt}</li>'
            front_html += '</ul>'
    elif card_type == "Cloze":
        front_html += card.get("front", "") # For Cloze, the front is the text with {{c1::cloze}}
        
    front_html += style_block
    front_html += '</div>'
    
    return front_html, back_html

def sync_cards(cards, target_deck, dry_run=False):
    # Step 1: Upload media
    media_mapping = {}
    for card in cards:
        local_img = card.get("mnemonic_image_path")
        if local_img and local_img not in media_mapping:
            if not dry_run:
                stored_name = store_media_file(local_img)
                if stored_name:
                    media_mapping[local_img] = stored_name
            else:
                print(f"[Dry-Run] Would upload media: {os.path.basename(local_img)}")
                media_mapping[local_img] = os.path.basename(local_img)
                
    # Step 2: Build Notes
    notes_payload = []
    for card in cards:
        card_type = card.get("type", "QA")
        tags = card.get("tags", ["anki-agent"])
        
        front_formatted, back_formatted = format_links_and_images(card, media_mapping)
        
        # Select note model
        if card_type == "Cloze":
            model_name = "Cloze"
            fields = {
                "Text": front_formatted,
                "Back Extra": back_formatted
            }
        else:
            model_name = "Basic"
            fields = {
                "Front": front_formatted,
                "Back": back_formatted
            }
            
        note = {
            "deckName": target_deck,
            "modelName": model_name,
            "fields": fields,
            "tags": tags,
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck"
            }
        }
        notes_payload.append(note)
        
    if dry_run:
        print(f"\n[Dry-Run] Validated {len(notes_payload)} cards ready for deck '{target_deck}':")
        for idx, note in enumerate(notes_payload):
            print(f"  {idx+1}. Type: {note['modelName']} | Tags: {note['tags']}")
            if note['modelName'] == "Cloze":
                print(f"     Text: {note['fields']['Text'][:100]}...")
            else:
                print(f"     Front: {note['fields']['Front'][:100]}...")
        return
        
    print(f"\nSyncing {len(notes_payload)} cards to deck '{target_deck}'...")
    ensure_deck_exists(target_deck)
    
    # Batch add notes
    results = request("addNotes", notes=notes_payload)
    
    success_count = sum(1 for r in results if r is not None)
    duplicate_count = sum(1 for r in results if r is None)
    
    print(f"Sync complete: {success_count} added, {duplicate_count} skipped/duplicates.")

def main():
    parser = argparse.ArgumentParser(description="Sync generated cards to local Anki.")
    parser.add_argument("--file", help="Path to JSON file containing cards.")
    parser.add_argument("--deck", default="AnkiCardmaker", help="Target deck name in Anki.")
    parser.add_argument("--dry-run", action="store_true", help="Print plans without importing to Anki.")
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            cards_data = json.load(f)
    else:
        # Read from stdin
        try:
            print("Reading card JSON from stdin...")
            cards_data = json.loads(sys.stdin.read())
        except Exception as e:
            print(f"Error reading JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)
            
    if not isinstance(cards_data, list):
        # Allow single card dictionary
        if isinstance(cards_data, dict):
            cards_data = [cards_data]
        else:
            print("Error: Input JSON must be a list of card objects", file=sys.stderr)
            sys.exit(1)
            
    sync_cards(cards_data, args.deck, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
