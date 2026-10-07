"use strict";
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
    say("World declaration loaded. Choose Inspect to learn what the portal offers.");
  } catch (error) {
    say("WORLD UNRESOLVED · " + error.message + ". You can return to the atlas.");
  }
}
loadWorld();
