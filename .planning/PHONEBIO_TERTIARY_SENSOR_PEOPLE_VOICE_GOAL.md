# PB-G3 / PB-G3a — Tertiary: sensors → people → voice (with vault + quant models)

**Locked:** 2026-07-24T17:18:24Z  
**Priority:** tertiary  
**Owner:** `phonebio`

## Operator lock

PhoneBio was to use **local sensors** to determine **how many people**, to help with **voice distinguishing**, as a **tertiary** goal — **while using the vault and quant models**.

## Runtime companions (PB-G3a)

| Piece | Role |
|---|---|
| **Vault** | User / FCO custody vault — private Merkle root stays user-side (Bitcoin-wallet style). Seal sensor/voice leaves. **Not** WorkOS Vault. |
| **Quant models** | Local quantized models (Ollama / ExecuTorch / browser edge path) for on-device sensor labels and low-bandwidth presence triage. Fail-soft. |
| **Local sensors** | Camera-free presence signals (acoustic, BLE/UWB, motion, …). |
| **People estimate** | Presence-class “how many nearby” — not identity. |
| **Voice distinguishing** | Tertiary aid for diarization / separating voice leaves. |

## Authority split

- Quant model labels = edge acceleration / context.
- Reviewed local tools/records = protocol & safety SoT.
- User vault = custody root authority for sealed leaves.

## Claim ceiling

- Do: sensors + quant models help estimate presence to improve voice distinguishing; leaves sealed in user vault.
- Do not: exact proven headcount; biometric ID; WorkOS as root vault; quant model as safety authority.

## Expanded by BioBridge (BB-EXP-1)

BioBridge took the **vault + quant/model-selection** ideas into a **GTM custody AI employee** (tokenized vault, per-agent Merkle roots, sealed golden-path model scoring). See `BIOBRIDGE_EXPANSION_LINEAGE.md`.

## On-device runtime (PB-G3a-ET / D17.7d)

Runs **within computers, phones, etc.** Worked example: **Samsung phones** with **ExecuTorch** + **quantized models**. Not a Samsung partnership claim. Portfolio: bioviz-tech `ON_DEVICE_EXECUTORCH_QUANT_EDGE_LOCK.json`.
