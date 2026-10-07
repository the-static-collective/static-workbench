"use strict";
import {
  readVoyage, beginRecording, recordDeparture, confirmArrival,
  setRecording, exportVoyage, eraseVoyage,
} from "./webz-storage.mjs";
// Two trusted first-party world documents. A door is an authored invitation,
// not destination authority or a signed reLATTE crossing.
const $ = (id) => document.getElementById(id);
const slug = document.body.dataset.webzWorld;
const KNOWN = {
  sanctuary: {
    id: "webz:the-static-collective/sanctuary",
    target_id: "webz:the-static-collective/orchard-022100",
    target_address: "webz::static/orchard/022100",
  },
  orchard: {
    id: "webz:the-static-collective/orchard-022100",
    target_id: "webz:the-static-collective/sanctuary",
    target_address: "webz::static/sanctuary",
  },
};
const ALLOWED_ROUTES = new Map([
  ["/webz/world/sanctuary", "webz:the-static-collective/sanctuary"],
  ["/webz/world/orchard", "webz:the-static-collective/orchard-022100"],
]);
const inspect = $("webz-inspect");
const cross = $("webz-cross");
const remain = $("webz-remain");
const returnButton = $("webz-return");
const status = $("webz-world-status");
const target = $("webz-door-target");
let manifest = null;
let door = null;
let inspected = false;

const beginRecorder = $("webz-begin-recording");
const pauseRecorder = $("webz-pause-recording");
const exportButton = $("webz-export-voyage");
const eraseButton = $("webz-erase-voyage");
const recorderStatus = $("webz-recording-status");
const STORAGE_KEY = "webz.voyage-local.v0";
function safeStorage() {
  try { return window.localStorage; }
  catch (_) {
    return {getItem(){throw new Error("blocked");},
      setItem(){throw new Error("blocked");},
      removeItem(){throw new Error("blocked");}};
  }
}
function updateRecorder(state = readVoyage(safeStorage())) {
  const usable = state.status === "recording" || state.status === "paused";
  beginRecorder.disabled = !manifest || state.status !== "off";
  pauseRecorder.disabled = !usable;
  pauseRecorder.textContent = state.status === "paused" ? "Resume recording" : "Pause recording";
  exportButton.disabled = !(usable || state.status === "corrupt");
  eraseButton.disabled = state.status === "off" || state.status === "unavailable";
  const count = state.record?.events?.length ?? 0;
  const hint = state.projection?.pending_departure_seq !== null &&
    state.projection?.pending_departure_seq !== undefined
    ? " · departure pending (not admitted)" : "";
  const message = state.status === "off"
    ? "Recording is off. Nothing is saved unless you choose Begin."
    : state.status === "recording"
      ? "LOCAL ONLY · Recording " + count + " navigation events" + hint + "."
      : state.status === "paused"
        ? "PAUSED · " + count + " local navigation events" + hint + "."
        : state.status === "corrupt"
          ? "CORRUPT LOCAL HISTORY · Export raw data or deliberately erase. No repair was inferred."
          : state.status === "unavailable"
            ? "STORAGE UNAVAILABLE · Navigation still works; this journey is not being recorded."
            : (state.error || "An unresolved local voyage awaits inspection.");
  recorderStatus.textContent = message;
  return state;
}
function downloadText(contents, filename, type) {
  const blob = new Blob([contents], {type});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
beginRecorder.addEventListener("click", () => {
  if (!manifest) return;
  updateRecorder(beginRecording(safeStorage(), manifest.world_id));
});
pauseRecorder.addEventListener("click", () => {
  const current = readVoyage(safeStorage());
  if (current.status === "recording" || current.status === "paused") {
    updateRecorder(setRecording(safeStorage(), current.status === "paused"));
  }
});
exportButton.addEventListener("click", () => {
  try {
    const current = readVoyage(safeStorage());
    if (current.status === "corrupt") {
      const raw = safeStorage().getItem(STORAGE_KEY);
      if (raw === null) throw new Error("Raw history is not available.");
      downloadText(raw, "webz-raw-local-recovery.txt", "text/plain");
    } else {
      downloadText(exportVoyage(safeStorage()), "webz-voyage-local-v0.json", "application/json");
    }
    updateRecorder();
  } catch (_) { recorderStatus.textContent = "Export unavailable; original local history was not changed."; }
});
eraseButton.addEventListener("click", () => {
  if (!window.confirm("Erase this browser-local webZ voyage? Export it first if you want to keep it.")) return;
  updateRecorder(eraseVoyage(safeStorage()));
});
updateRecorder();

// A browser-local, tab-scoped navigation handoff is not a signed receipt.
// It prevents an unrelated direct world visit from claiming a prior portal
// departure. Its short wall-clock expiry is NOT voyage identity or order.
const HANDOFF_KEY = "webz.portal-handoff/v0";
function markPortalDeparture(trace, from_world_id, to_world_id, door_id) {
  const seq = trace.projection?.pending_departure_seq;
  if (trace.status !== "recording" || !Number.isSafeInteger(seq)) return false;
  try {
    window.sessionStorage.setItem(HANDOFF_KEY, JSON.stringify({
      schema: "webz/portal-handoff/v0",
      from_world_id, to_world_id, door_id, departure_seq: seq, issued_at_ms: Date.now(),
    }));
    return true;
  } catch (_) { return false; }
}
function matchingPortalHandoff(trace, arrived_world_id) {
  if (trace.status !== "recording" || trace.projection?.pending_departure_seq === null) return false;
  try {
    const raw = window.sessionStorage.getItem(HANDOFF_KEY);
    if (!raw) return false;
    const packet = JSON.parse(raw);
    const issued = packet.issued_at_ms;
    const age = Date.now() - issued;
    const keys = ["schema","from_world_id","to_world_id","door_id","departure_seq","issued_at_ms"];
    const departure = trace.record.events.find((event) =>
      event.seq === trace.projection.pending_departure_seq && event.kind === "departed");
    if (!departure || !packet || typeof packet !== "object" || Array.isArray(packet) ||
        Object.keys(packet).length !== keys.length ||
        !keys.every((key) => Object.hasOwn(packet,key)) ||
        packet.schema !== "webz/portal-handoff/v0" ||
        !Number.isSafeInteger(issued) || age < 0 || age > 120000 ||
        packet.from_world_id !== departure.from_world_id ||
        packet.to_world_id !== departure.to_world_id ||
        packet.to_world_id !== arrived_world_id ||
        packet.door_id !== departure.door_id ||
        packet.departure_seq !== departure.seq) return false;
    const fromSlug = departure.from_world_id === KNOWN.sanctuary.id ? "sanctuary"
      : departure.from_world_id === KNOWN.orchard.id ? "orchard" : null;
    if (!fromSlug) return false;
    // The browser documents the actual source page of the navigation.
    return document.referrer === window.location.origin + "/webz/world/" + fromSlug;
  } catch (_) { return false; }
}
function clearPortalHandoff() {
  try { window.sessionStorage.removeItem(HANDOFF_KEY); } catch (_) {}
}
function say(message) { status.textContent = message; }
function closeDoor() {
  inspected = false;
  cross.disabled = true;
  target.hidden = true;
  target.textContent = "";
}
function inspectDoor() {
  if (!door || !manifest) return;
  target.textContent = "DOOR: " + door.door_id + "\nDESTINATION: " +
    door.to_address + "\nDECLARED WORLD: " + door.to_world_id +
    "\nWHAT CARRIES: NONE\nNo reLATTE crossing, permission or admission has occurred.";
  target.hidden = false;
  inspected = true;
  cross.disabled = false;
  say("Portal inspected. You may cross, remain, or return to the atlas.");
}
inspect.addEventListener("click", inspectDoor);
if (returnButton) returnButton.addEventListener("click", inspectDoor);
remain.addEventListener("click", () => {
  closeDoor();
  say("REMAIN · You are still in this world. No crossing occurred.");
});
cross.addEventListener("click", async () => {
  if (!inspected || !door || !manifest || cross.disabled) return;
  cross.disabled = true;
  say("Resolving the declared destination. No departure has been recorded yet…");
  try {
    // Never navigate to a user-supplied URL or to a route synthesized from input.
    const response = await fetch("/api/webz/resolve?address=" +
      encodeURIComponent(door.to_address), {headers:{Accept:"application/json"}});
    if (!response.ok) throw new Error("Resolver unavailable");
    const resolved = await response.json();
    const allowed = KNOWN[slug];
    if (!allowed ||
        door.to_world_id !== allowed.target_id ||
        door.to_address !== allowed.target_address ||
        resolved.status !== "resolved" ||
        resolved.typed_address !== door.to_address ||
        resolved.world_id !== door.to_world_id ||
        ALLOWED_ROUTES.get(resolved.entry_route) !== resolved.world_id) {
      throw new Error("The destination has no trusted local address.");
    }
    // An intentional second click is the only portal navigation trigger.
    const trace = recordDeparture(safeStorage(), manifest.world_id, door.to_world_id, door.door_id);
    updateRecorder(trace);
    markPortalDeparture(trace, manifest.world_id, door.to_world_id, door.door_id);
    if (["corrupt","unavailable","unresolved","pending"].includes(trace.status)) {
      say("BROWSING ONLY · The local trace was not advanced (" + trace.status + "). You can still enter.");
    }
    window.location.assign(resolved.entry_route);
  } catch (error) {
    say("UNRESOLVED / HOLD · " + error.message +
      ". You remain here; the destination was not entered.");
    cross.disabled = false;
  }
});

async function loadWorld() {
  inspect.disabled = true;
  cross.disabled = true;
  if (returnButton) returnButton.disabled = true;
  if (!KNOWN[slug]) { say("Unknown local world. Return to the atlas."); return; }
  try {
    const response = await fetch("/api/webz/worlds/" + slug, {
      headers: {Accept:"application/json"},
    });
    if (!response.ok) throw new Error("World declaration unavailable");
    const document = await response.json();
    if (document.schema !== "webz/world/v0" ||
        document.world_id !== KNOWN[slug].id ||
        !Array.isArray(document.doors) ||
        document.doors.length !== 1 ||
        document.doors[0].carry_mode !== "none" ||
        document.doors[0].to_address !== KNOWN[slug].target_address ||
        document.doors[0].to_world_id !== KNOWN[slug].target_id) {
      throw new Error("The declaration did not match the installed world.");
    }
    manifest = document;
    door = document.doors[0];
    inspect.disabled = false;
    if (returnButton) returnButton.disabled = false;
    const earlier = readVoyage(safeStorage());
    if (matchingPortalHandoff(earlier, manifest.world_id)) {
      const confirmed = confirmArrival(safeStorage(), manifest.world_id);
      updateRecorder(confirmed);
      if (confirmed.status === "recording" &&
          confirmed.projection.pending_departure_seq === null) clearPortalHandoff();
    } else {
      // A direct URL visit or expired/mismatched handoff cannot turn an
      // earlier intention into an observed portal arrival.
      updateRecorder(earlier);
    }
    say("World declaration loaded. Choose Inspect to learn what the portal offers.");
  } catch (error) {
    say("WORLD UNRESOLVED · " + error.message + ". You can return to the atlas.");
  }
}
loadWorld();
