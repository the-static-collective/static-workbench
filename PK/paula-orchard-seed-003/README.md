# Paula Story Workbench

> **Unbriefed handoff:** if someone just gave you this folder/ZIP and you are using ChatGPT, upload it and say whatever comes naturally. ChatGPT should begin with [`GIVE_THIS_TO_CHATGPT.md`](GIVE_THIS_TO_CHATGPT.md). You do not need to understand the machinery first.

A small story-to-video desk for turning daily dramatic thoughts into short-form narrative video packets.

**Default loop**

```text
storydrop
  -> story kernels
  -> human KEEP / HOLD
  -> biblical resonance aperture
  -> episode board
  -> Flow-ready shot prompts
  -> generated clips
  -> scene assembly
```

This repo intentionally borrows only the useful membrane from MEMENTO: raw testimony is not automatically story canon, retrieved resonance is not authority, and the human keeps the continuation decision.

## Tonight: start here

1. Install Node.js 20+ if it is not already present.
2. Double-click `START_PAULA.bat` on Windows, or run `npm start` in this folder.
3. The Story Desk opens at `http://127.0.0.1:3333`.
4. Speak/type a raw story thought and click **Save + Build ChatGPT Packet**.
5. Paste the packet into a ChatGPT conversation/project that uses `CHATGPT_PROJECT_INSTRUCTIONS.md` as its instructions.
6. Ask ChatGPT to return the `STORY_CARD_JSON` block.
7. Paste that JSON into the Story Desk and click **Save Story Card**.
8. Click **Build Flow Batch**. Copy the shot prompts into Google Flow.
9. Put downloaded clips in `generated/clips/<story-id>/` and use Flow Scenebuilder for the first assembly. If `ffmpeg` is installed, `npm run assemble -- stories/<file>.json` can also make a simple cut locally.

The first success criterion is deliberately small: **one real thought becomes one kept kernel, one coherent storyboard, and one finished short.**

## Conversational commands

These are optional shorthand when talking to ChatGPT:

- `STORYDROP:` raw thought — harvest without polishing the witness away.
- `KERNELS` — show 1–3 strongest dramatic kernels.
- `KEEP <id>` — choose which kernel may continue.
- `HOLD` — preserve it without forcing a story yet.
- `FRAME IT` — map the kept kernel to biblical narrative/resonance frames.
- `BOARD IT` — produce a short-form episode storyboard.
- `FLOW IT` — compile Flow-ready prompts.
- `ALT TAKE` — change execution while preserving the kept kernel.
- `FICTIONALIZE` — aggressively de-identify real-life source material for publication.

## Core boundaries

- `RAW TRACE != FICTIONAL STORY`
- `BIBLICAL RESONANCE != DIVINE VERDICT`
- `RETRIEVED FRAME != CLAIM OF FULFILLMENT`
- `MODEL SUGGESTION != KEEP`
- `PRIVATE LIFE != PUBLICATION PERMISSION`
- `KEEP = this exact dramatic kernel may continue`

## Directories

- `inbox/` raw storydrops, preserved as received
- `stories/` kept/held structured story cards
- `prompts/` reusable ChatGPT handoffs
- `templates/` machine-readable shapes
- `generated/boards/` Flow prompt batches
- `generated/clips/` downloaded generations
- `generated/assemblies/` local assembly outputs/manifests
- `docs/` house style, call runbook, and architecture receipt

## Optional independent orchard / executable local responsibility gate

Start with a story. If you want to explore experimental Collective branches or prepare exact local keep/shareable-export receipts, see [`ORCHARD_SEED_001.md`](ORCHARD_SEED_001.md) and run `npm run test:orchard`. The kernel is local-only and cannot publish, bill, contact customers, authenticate people, install remote code, or govern the existing Story Desk; all these boundaries are explicit in that document.
