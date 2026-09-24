# Tonight's Work Call — Runbook

The goal of the call is not to explain the whole architecture. It is to leave Paula able to repeat the loop without assistance.

## 1. Open the desk

Run `START_PAULA.bat` or `npm start`.

Show only four actions:

1. tell the story;
2. paste the ChatGPT packet;
3. KEEP a kernel;
4. generate the Flow batch.

Everything else is backstage.

## 2. Put the instructions in ChatGPT

Create a ChatGPT Project or dedicated conversation and paste `CHATGPT_PROJECT_INSTRUCTIONS.md` into its instructions/context. If GitHub access is connected, point the conversation at this repo so ChatGPT can read the templates directly.

## 3. Do one live STORYDROP

Paula talks naturally. Do not make her pre-format it.

Use the desk's **Save + Build ChatGPT Packet** button, paste that packet into ChatGPT, and let it return 1–3 kernels.

The important teaching moment is the distinction:

> "ChatGPT is showing possible stories. You decide which one gets to become the story."

## 4. KEEP one kernel

Paula chooses the kernel that feels alive. If none do, use `ALT KERNELS` rather than polishing a dead one.

Then ask:

`KEEP K2. FRAME IT. BOARD IT. FLOW IT. Return STORY_CARD_JSON.`

## 5. Save the story card

Paste the JSON back into the local Story Desk and save it. The repo now contains the raw trace separately from the selected creative continuation.

## 6. Generate a tiny first batch in Flow

Start with a mixed batch:

- one HERO shot for the recurring face/character;
- one BRIDGE shot if a controlled transition matters;
- several cheap TEXTURE shots for setting, symbols, inserts, reactions, or atmosphere.

Do not chase perfect continuity across every shot. Spend continuity effort only where the viewer will notice it.

## 7. Assemble

For the first session, Flow Scenebuilder is the lowest-friction editor: arrange, trim, preview, and export there.

Later, the Toaster can become the local deterministic assembly/render layer once the actual recurring needs are visible.

## The call is successful when

Paula can independently repeat:

```text
thought -> kernels -> KEEP -> board -> Flow prompts -> clips -> scene
```

Do not add more machinery during the call unless that loop fails for a concrete reason.
