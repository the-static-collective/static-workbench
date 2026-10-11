# Google Flow Strategy

This file records the current production rule for the workbench.

## Three shot classes

### HERO
Use when character/object continuity matters. Prefer reusable ingredients/references and an 8-second generation, then trim to the useful beat.

### BRIDGE
Use when the start/end composition or action transition matters. Prefer Frames-to-Video at 4, 6, or 8 seconds.

### TEXTURE
Use when continuity is cheap: dust, doors, cups, hands, sky, market inserts, symbolic images, reaction silhouettes, establishing shots. Prefer 4-second text-to-video generations.

## Why this mix

Current Flow documentation supports 4s/6s/8s text-to-video and Frames-to-Video in Veo 3.1 Lite, while Ingredients/References-to-Video is 8 seconds. The workbench therefore spends the longer reference-aware generations on continuity-critical shots and uses short generations for everything else.

## Prompt anatomy

Every copy-ready prompt should clearly state:

1. subject;
2. action;
3. environment;
4. camera/framing or movement;
5. lighting;
6. material/visual texture;
7. one dominant emotional beat.

Avoid contradictory guidance. Avoid three dramatic beats inside one 4-second shot.

## Continuity trick

Save a useful frame from a successful clip and reuse it as a later ingredient/start/end frame. Build continuity out of successful generations instead of describing the same face from scratch every time.

## Assembly

Use Flow Scenebuilder first: arrange clips, trim them, preview the sequence, and download the scene. Local Toaster-style deterministic assembly is a later layer, not a prerequisite.

## Source notes

- Google Flow Help — Create videos in Google Flow: https://support.google.com/flow/answer/16353334
- Google Flow Help — Models & supported features: https://support.google.com/flow/answer/16352836
- Google Flow Help — Edit videos & build scenes: https://support.google.com/flow/answer/16935718

Check the active model and current credit cost in Flow before a batch; costs and feature availability can change.
