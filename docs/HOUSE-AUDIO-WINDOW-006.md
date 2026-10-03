# HOUSE AUDIO WINDOW 006 — First-Listen Radio Enters the Room

## Claim

The House can now admit a bounded local audio specimen and carry it through the same temporal-isolation law already proven with visual artifacts.

~~~
configured local root
      ↓
root-relative audio file
      ↓
human-declared start/end ms
      ↓
Autodisco canonical AUDIO WINDOW
      ↓
House materializes exact WAV bytes once
      ↓
two first-listen booths
   ┌──────────┴──────────┐
   ↓                     ↓
Static Sam             Juniper
isolated listen        isolated listen
   ↓                     ↓
sealed first A         sealed first B
   └──────────┬──────────┘
              ↓
      audio window closes
              ↓
        response cross-read
              ↓
       lingering intrigue?
              ↓
       proposed House door
~~~

## Source boundary

The user selects one configured Workbench root, one root-relative audio file, integer start/end milliseconds, and one opaque window label.

Workbench resolves the source through its existing root confinement. Paths outside the configured root are refused.

The source path remains House-local. The listener packet does not receive the absolute path, repository path, artist biography, album/catalog history, lyrics, prior DJ transcripts, or House conversation history.

LOCAL SOURCE PATH != LISTENER CONTEXT

## Materialization

Autodisco AUDIO WINDOW returns a canonical WAV plus a content-derived window identity.

Workbench verifies the returned byte length and SHA-256, writes the WAV beneath:

~~~
<state_dir>/doorhouse-audio/<local-receipt-id>/<window-id>.wav
~~~

and removes the base64 bytes from ordinary House state.

The witness retains the window id, canonical audio digest, materialized local path, exact requested bounds, canonical format facts, extraction facts, declared label, and base64 transport digest.

When a first-listen call needs the audio, Workbench re-reads the materialized WAV, verifies its digest and size, reconstructs the transport, and only then invokes Autodisco.

## Multiple windows

Audio witnesses are keyed by window_id, not by one mutable slot.

A receipt may therefore retain window A, window B, window C, and later specimens without rewriting earlier ones. The newest window becomes the current UI specimen while previous windows and their receipts remain historical evidence.

## Audio LOOK TWICE witnesses

Each audio pair uses separate durable kinds:

- audio_window:<window-id>
- audio_look_twice_pair:<pair-id>
- audio_look_twice_first:<pair-id>:static-sam
- audio_look_twice_first:<pair-id>:juniper
- audio_look_twice_dialogue_packet:<pair-id>
- audio_look_twice_dialogue:<pair-id>

A cross-read is refused unless the exact pair has two sealed first listens.

The dialogue packet is also checked for audio transport data. The audio window is not allowed back into the conversation stage.

## Honest silence

If no real listener model is available:

~~~
audio window exists
pair exists
first_responses = []
cross-read remains locked
~~~

If two first listens exist but no real dialogue model is available:

~~~
dialogue packet exists
dialogue does not
~~~

No fake listening and no fake exchange.

## House language

After two real first listens:

> **Two strangers heard the same slice. Neither heard the other.**

When a real cross-read preserves lingering intrigue:

> **They heard it twice. Something was still ringing.**

That second letter may contain a returned door_seed, but it remains a proposed door. The human still has to open, inspect, select, and cross.

## Radio UI

Each agency receipt now has an AUDIO WINDOW control:

~~~
root
relative file path
start ms
end ms
opaque window label
~~~

Then:

~~~
Cut bounded audio window
→ FIRST-LISTEN RADIO · prepare two audio booths
→ Play window independently to both listeners
→ Unlock audio cross-read · window stays closed
~~~

A second window can be cut from the same receipt without mutating the first.

## Cross-repo proof

The canonical Workbench smoke generates an actual stereo 44.1 kHz WAV, then executes the landed Autodisco runtime:

~~~
generated local WAV
→ AUDIO WINDOW exact sample slice
→ House materialization
→ digest verification
→ audio LOOK TWICE pair
→ two booth identities
→ no-key runtime
→ exactly zero fabricated first listens
~~~

This sits beside the existing real House → GHoT → Haunted Toaster → returned SVG → visual LOOK TWICE proof.

## Laws

~~~
WINDOW != WHOLE TRACK
LOCAL SOURCE PATH != LISTENER CONTEXT
SOURCE DIGEST != WINDOW DIGEST
WINDOW WITNESS != FIRST LISTEN
SAME AUDIO WINDOW != SHARED CONTEXT
FIRST LISTEN PRECEDES CROSS-READ
SEALED != SHARED
AUDIO WINDOW IS NOT REOPENED
SIMULATION != FIRST LISTEN
SIMULATION != AUDIO DIALOGUE
LINGERING INTRIGUE != SOURCE TRUTH
DOOR SEED != CROSSING
MEMORY != AUTHORITY
~~~

## Next earned door

The next move is no longer protocol research.

It is broadcast assembly: choose a real catalog track, cut one bounded window, acquire two real sealed first listens, cross-read them, preserve the surviving intrigue, and assemble the first short interstitial around the actual audio window and its receipts.

That is the first honest radio segment.
