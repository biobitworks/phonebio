# BB-EXP-1 — BioBridge expands PhoneBio tertiary (vault + quant)

**Locked:** 2026-07-24T17:19:27Z

## Operator lock

**BioBridge expanded on** the PhoneBio tertiary path (local sensors → people estimate → voice distinguishing **while using the vault and quant models**).

## Expansion map

| PhoneBio (PB-G3/G3a) | BioBridge expansion |
|---|---|
| User custody vault seals leaves | Tokenized private contact fields vaulted; public hash rotates on touch; unlock = custody event |
| Merkle root user-side | Per-agent Merkle roots / self-sealing agent chains |
| Local quant models (edge triage) | Glasswork multi-model score vs vault-sealed golden root — cheapest that passes |
| Presence-class “how many people” | GTM people/company graph with vaulted PII (different “people” sense) |
| Field voice/sensor context | GTM AI employee: find → qualify → route → prove |

## Surfaces

- Live: https://biobridge-pipeline.kylon.app / `/final-demo`
- Method: FCO https://doi.org/10.5281/zenodo.21210575
- Package: `/Users/byron/projects/inbox/biobridge-package.tar.gz` (local archive)

## Ceiling

Do not conflate PhoneBio sensor people-count with BioBridge lead-graph headcounts. BioBridge does not claim phone-sensor voice diarization.
