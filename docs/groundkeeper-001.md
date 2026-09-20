# GROUNDKEEPER-001 — Synthetic Field Laboratory

**Status:** experimental HOUSE-owned instrument; simulated and operator-triggered only.

GROUNDKEEPER-001 turns a bounded synthetic ground signal into two coupled creative instruments (sound and visual), compares three explicit connection-graph changes, and emits a deterministic, content-addressed receipt. It does not claim to detect seismic hum, Schumann resonances, machine sentience, or a TranchNOSE optical field object.

## First flight in the HOUSE browser

Start the normal Static Workbench on the dedicated Linux machine and open its existing loopback desk. Select **GROUNDKEEPER** in the navigator or **Open GROUNDKEEPER field lab** on the House action grid. Enter a printable synthetic seed and select **Run synthetic first flight**. Inspect the musical phrase, 8x8 visual frame, baseline measurements, three candidate graph deltas, and exact receipt digest.

**Copy complete experimental receipt** exports the displayed JSON for separate inspection; **Copy graph for human review** exports a candidate declaration. The browser does not record environmental audio, save the receipt to the HOUSE journal, invoke GRAFT/Dogram, install software, create a service, publish work, or change project state. Copying a candidate does not admit it to a project.

The read-only, deterministic JSON endpoint is `GET /api/groundkeeper/first-ignition?seed=static-first-ignition`. The seed is capped at 128 printable characters. This endpoint deliberately accepts no arbitrary sensor data or project command.

## Headless first flight

From the installed Workbench checkout (Python 3.11+):

```sh
python -m static_workbench.groundkeeper --seed static-first-ignition --output ~/groundkeeper-first.json
python -m static_workbench.groundkeeper --replay ~/groundkeeper-first.json
```

The first command creates **one new explicitly named file** and refuses to overwrite an existing path. Omit `--output` to print JSON to stdout without writing a file. The replay command checks the receipt digest, sample digest, seeded signal (if synthetic), graphs, derived music, visual frames, comparisons, and complete exact serialized outcome.

To feed a user-selected, already normalized recording-derived signal, create a small JSON file:

```json
{"samples":[0.1,0.2,0.0,-0.1,0.2,0.4,0.0,-0.2],"label":"bench-contact-mic-unverified"}
```

Then run:

```sh
python -m static_workbench.groundkeeper --samples-json ./explicit-samples.json --output ~/groundkeeper-provided.json
```

The input must contain exactly `samples` and `label`, include 8–256 finite numeric samples in [-1, 1], and fit within 64 KiB. The source is recorded as `provided-unverified`: a label and a sample digest are **not** proof of where a real physical signal came from. There is no microphone capture or calibration in this slice. Do not provide private recordings without reviewing what the exported samples disclose.

## The relation experiment

The fixed instrument list is `ground`, `sound`, and `visual`. The baseline graph has `ground>sound`, `sound>visual`, and `visual>sound`. Each directed edge consumes **previous-tick state**, giving the feedback loop a defined delay and bounded tanh dynamics. Visual frames and note events are declared artistic mappings of calculated state.

The three unreviewed variants:

1. Add a direct `ground>visual` edge.
2. Remove the `visual>sound` feedback edge (ablation).
3. Increase the weight of the `visual>sound` feedback edge.

Each variant records a complete graph digest, a trajectory digest, mean absolute state delta, sound and visual energy deltas, and final state. A difference is an observed **simulation result**, not an artistic ranking, evidence of physical causality, or authority to alter the host.

The comparator preserves the original graph. No synthetic candidate silently becomes a reusable capability. Negative controls and ablations can produce useful results without being selected.

## Provenance and neighboring projects

- **HOUSE:** experimental local habitat and operator surface. Existing project-owned receipts and authorization are unchanged.
- **TranchNOSE:** research inspiration only. Its original optical-field hypotheses, physical no-cheating tests, and information-capacity controls remain independent. This software simulation does not satisfy Experiment 001.
- **GRAFT:** human-reviewed proposed capability handoff. GROUNDKEEPER's JSON may be copied as context, but there is no automatic candidate import/admission, and the current GRAFT native candidate table remains tied to a saved Maxhinal ride.
- **Dogram:** structural calculation may be requested separately after a person defines the graph and its comparison. The present energy deltas are not Dogram receipts.
- **GOATnote / Static Live / Toaster:** potential future explicit output adapters, not invoked here.

## Next admitted stages (not implemented by 001)

1. Add an opt-in, calibrated contact-microphone/geophone adapter, with an explicit device and capture duration, sample rate, gain/normalization, environmental metadata, physical safety rules, and privacy controls.
2. Store exact experiment receipts in a separate append-only HOUSE experimental shelf; detect source drift and fail replay rather than invent observations.
3. Implement a human-reviewed GROUNDKEEPER -> saved GRAFT ride/candidate bridge with typed provenance and an independent Dogram witness when useful.
4. Add a versioned, consent-gated compound-instrument library. Each admitted instrument declares inputs, outputs, effects, resource limits, cancel/reconcile behavior, and parent receipt. Experimental self-proposals run within a CPU/memory/time/disk budget, never with implicit install, shell, network, publication, or hardware rights.
5. Evaluate relational reconstruction with frozen recognition criteria, swap and ablation controls, alternative hidden-state explanations, and a clean separation between software feedback results and TranchNOSE's physical claims.

**Stop boundary:** No unattended sensing, autonomous hardware control, arbitrary subprocess composition, silent cross-project writes, or automatic growth of operator privileges. The machine may propose new relationships; admission remains an explicit separate act.
