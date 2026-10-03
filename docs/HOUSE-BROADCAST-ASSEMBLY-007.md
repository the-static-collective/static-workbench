# HOUSE BROADCAST ASSEMBLY 007 — A Radio Episode Becomes Playable

## Claim

A completed First-Listen Radio evidence chain can now become one portable local episode without rewriting any of the evidence that produced it.

```text
AUDIO WINDOW
    ↓
Static Sam sealed first listen
Juniper sealed first listen
    ↓
sealed audio cross-read
    ↓
Autodisco BROADCAST ASSEMBLY
    ↓
House verifies bundle
    ↓
broadcast_episode witness
    ↓
PLAY EPISODE
```

## Required evidence

The House refuses assembly until the current audio pair has:

- one exact witnessed audio window;
- one exact audio LOOK TWICE pair;
- exactly two sealed first listens;
- one sealed dialogue packet;
- one sealed dialogue.

The episode must bind the same:

- window id;
- audio digest;
- pair id;
- two first-response ids;
- dialogue id.

```text
PACKET != FIRST LISTEN
DIALOGUE PACKET != DIALOGUE
ASSEMBLY != MISSING EVIDENCE
```

## Portable bundle

Autodisco writes beneath House state:

```text
<state_dir>/doorhouse-radio/<receipt-id>/<episode-id>/
    episode.json
    window.wav
    index.html
```

Workbench verifies:

- the bundle cannot escape that directory;
- all declared files exist;
- the copied WAV still hashes to the witnessed audio digest;
- the manifest digest matches;
- the player digest matches.

The House then stores a separate witness:

```text
broadcast_episode:<episode-id>
```

Assembly is therefore downstream of first listening and dialogue rather than an edit of either one.

## Local player

The House exposes read-only loopback routes for:

- the player;
- the canonical WAV;
- the episode manifest.

Opening or playing those routes does not mutate House state.

The browser player sequences:

1. deterministic station intro;
2. exact witnessed audio window;
3. preserved first-listen closing lines;
4. preserved cross-read turns;
5. preserved intrigue/outro.

Local browser Speech Synthesis may speak the text.

That voice is a playback projection only.

```text
ASSEMBLY != VOICE RENDER
BROWSER VOICE != SEALED LISTENER
PLAYBACK != BROADCAST OCCURRENCE
```

## House language

When assembly succeeds the House receives a new sealed letter:

> **The station has something you can press Play on.**

Opening that letter exposes doors to:

- play the episode;
- offer it to Static Live;
- cut another window.

The episode itself does not automatically start Static Live or OBS.

## CI evidence split

The canonical cross-repo smoke makes two different claims and keeps them visibly separate.

### Runtime absence proof

With no model key:

```text
real generated WAV
→ real AUDIO WINDOW
→ real audio LOOK TWICE pair
→ first_responses = []
```

No fake listener is produced.

### Assembly integration proof

After that absence proof completes, CI creates explicitly labeled **synthetic fixture** first-listen and dialogue evidence.

Those fixtures are used only to exercise:

```text
landed Autodisco BROADCAST ASSEMBLY
→ episode.json
→ exact window.wav
→ index.html
→ House broadcast_episode witness
```

The synthetic fixture is never presented as evidence that a real listener heard the CI audio.

```text
SYNTHETIC FIXTURE != LIVE LISTENER EVIDENCE
```

## Static Live boundary

Static Live already owns broadcast occurrence:

- OBS preflight;
- recording;
- stream state;
- scene changes;
- preservation receipt.

This episode is declared media that may later be admitted into that runtime.

```text
AUTODISCO EPISODE != STATIC LIVE OCCURRENCE
DECLARED MEDIA != ACTUAL PLAYBACK
EPISODE WITNESS != BROADCAST RECEIPT
```

## Laws

```text
ASSEMBLY != FIRST LISTEN
ASSEMBLY != DIALOGUE
ASSEMBLY != VOICE RENDER
BROWSER VOICE != SEALED LISTENER
WINDOW != WHOLE TRACK
EPISODE != BROADCAST OCCURRENCE
PLAYBACK != REMOTE DELIVERY
PLAYBACK != HOUSE MUTATION
SYNTHETIC FIXTURE != LIVE LISTENER EVIDENCE
MEMORY != AUTHORITY
```

## Next earned door

The next crossing is not another player.

It is a bounded Static Live media handoff:

```text
Autodisco episode digest
    ↓
Static Live declared media slot
    ↓
operator chooses PLAY
    ↓
OBS/local media executes
    ↓
Static Live occurrence receipt
```

That will distinguish a playable episode artifact from an episode that was actually broadcast or recorded.
