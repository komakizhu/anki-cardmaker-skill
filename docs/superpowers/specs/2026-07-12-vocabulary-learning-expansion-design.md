# Vocabulary Learning Expansion

## Scope

Apply the expansion only to vocabulary cards and English Cloze cards whose deleted target is a word or phrase. Do not add these sections to Chinese cards, general QA cards, or ordinary choice cards.

## Card Sections

After the dictionary block, render the five lexical-relation items inside one rounded block titled `词汇关系`, with small labels for each populated item:

1. Synonyms / antonyms
2. Near synonyms
3. Confusable words
4. Collocations
5. Word roots and affixes

Three bilingual example sentences and other meanings remain separate rounded blocks.

Empty sections are omitted. The existing answer, dictionary, explanation, and mnemonic blocks remain unchanged.

## Data Contract

Optional fields:

- `synonyms`: string or list of strings
- `antonyms`: string or list of strings
- `near_synonyms`: string or list of strings
- `confusable_words`: string or list of strings
- `collocations`: string or list of strings
- `word_root`: string
- `word_affixes`: string
- `example_sentences`: list of at least three strings
- `example_sentences_zh`: list of at least three strings
- `other_meanings`: string or list of strings

Example translations must align by index. The renderer shows no example block when fewer than three English examples are supplied, preventing incomplete study material from looking authoritative.

## Target Detection

Vocabulary cards are identified by an explicit `word` field or vocabulary-oriented tags/fields. English Cloze cards use the first deleted term as the target when the target contains Latin letters and is not a sentence-length phrase. Chinese Cloze targets do not receive the expansion.

## Quality Rules

- All related words and collocations must match the current sense where context is available.
- Other meanings must be labeled with part of speech when known.
- No empty rounded boxes.
- Existing bilingual suppression rules remain in effect for Chinese source text.

## Verification

- Validate the expanded JSON fields.
- Verify that normal QA and choice cards contain none of the new sections.
- Verify that vocabulary and English Cloze cards render each populated section independently.
- Generate a static preview and sync the practice deck while preserving review history.
