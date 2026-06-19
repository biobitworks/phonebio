# Gregg + SeedGraph Ingest Plan

## Current State

PhoneBio has not yet ingested the full text and images from the Gregg shorthand
website through SeedGraph. The current implementation is a deterministic,
Gregg-inspired compressor:

- `fieldbio/shorthand.py`
- `content/shorthand/lexicon.json`
- `functions/vapi-webhook.ts`

That path supports brief forms, phrase blending, vowel omission, affix
compression, filler removal, and measurement extraction. It is useful for field
notes, but it is not a full Gregg shorthand recognizer or dictionary-backed
transcriber.

## Better Open Sources To Evaluate

- `https://greggshorthand.github.io/anindex.html` — concept/reference corpus
  with text and scanned shorthand pages.
- `https://github.com/richyliu/greggdict` — MIT-licensed web search/viewer for
  Gregg dictionary material, with OCR process notes.
- `https://halplatt.github.io/GreggDictionary/GreggDictionarypd.html` —
  searchable Gregg dictionary surface with multiple series/categories.
- `https://github.com/grascii` — Grascii organization with dictionaries,
  datasets, tokenizer work, RPC, and outline-rendering tools.
- `https://github.com/grascii/editor` — turns Grascii text into Gregg outline
  images; useful for offline training examples and visual validation.

Before importing any scanned dictionary images, keep a separate license/custody
row for source assets. The open-source app code can be MIT while the underlying
dictionary scans may have separate copyright/public-domain questions.

## What We Need

1. **SeedGraph custody ingest.** Import website HTML, linked PDFs/images, and
   open-source dictionary datasets as source assets with SHA-256 hashes, source
   URLs, license notes, and extraction identity. This should happen in
   SeedGraph, not ad hoc inside PhoneBio.
2. **Dictionary table.** Build a local `gregg_entries` artifact with word,
   phrase, series, shorthand outline asset, Grascii token if available,
   phoneme/syllable form, source id, and confidence.
3. **Syllable/phoneme bridge.** Use a deterministic pipeline:
   `speech text -> normalized phrase -> phonemes/syllables -> Gregg/Grascii
   candidate -> compact field token -> expanded text`.
4. **Science lexicon overlay.** Add biology/protocol terms that are absent from
   historical shorthand dictionaries: SDS, PPE, formaldehyde, transect, GNSS,
   barometer, UWB, LiDAR, centrifuge, preservative, voucher, aliquot.
5. **Round-trip tests.** Every compressed note should preserve safety-critical
   fields: substance, amount, exposure route, location, protocol id, device,
   sensor reading, units, and escalation condition.
6. **Nebius role.** Use Nebius for non-safety candidate generation, ambiguity
   ranking, multilingual paraphrase, and evaluation. Do not let Nebius override
   source-backed protocol/SDS answers.

## Runtime Boundary

For v1, PhoneBio should continue to use deterministic local shorthand at call
time. Full Gregg image/text ingestion is an offline corpus-building task. The
phone call should only consume the reviewed lexicon/dictionary artifacts, not
scrape websites or run image OCR live.
