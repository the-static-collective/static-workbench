"use strict";
// STATIC-ARG-002: manual, locally persistent fictional navigation; render as plain text.
let token = "";
let state = null;
let worldId = null;
const $ = (id) => document.getElementById(id);
const ROOM_IDS = ["threshold", "workshop", "garden", "archive"];
const OBJECT_IDS = ["rule", "machine", "seed", "chronicle"];

function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}

async function api(path, payload) {
  const options = { headers: { Accept: "application/json" } };
  if (payload !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.headers["x-workbench-session"] = token;
    options.body = JSON.stringify(payload);
  }
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "The local World could not be opened.");
  return data;
}

function message(text, error = false) {
  $("world-status").textContent = text;
  $("world-status").classList.toggle("world-error", error);
}

async function act(action, target) {
  const button = document.activeElement;
  if (button && button.tagName === "BUTTON") button.disabled = true;
  try {
    const next = await api("/api/arg/worlds/" + worldId + "/play", {
      action, expected_room: state.room_id, target,
    });
    state = next;
    render();
    message(action === "travel" ? "You entered " + room().title + "." : "The object is recorded in your local field notes.");
  } catch (error) {
    message(error.message, true);
    // A stale view is read again rather than inventing a successful traversal.
    try { state = await api("/api/arg/worlds/" + worldId + "/play"); render(); }
    catch (_) { /* keep the visible error */ }
  } finally {
    if (button && button.tagName === "BUTTON" && button.isConnected) button.disabled = false;
  }
}

function room() {
  return state.rooms.find((entry) => entry.id === state.room_id);
}

function renderMap(active) {
  const map = $("world-map");
  map.replaceChildren();
  for (const place of state.rooms) {
    const button = node("button");
    button.type = "button";
    const current = place.id === active.id;
    const adjacent = active.neighbors.includes(place.id);
    button.dataset.active = String(current);
    button.disabled = current || !adjacent || place.locked;
    button.append(
      node("strong", place.title),
      node("small", current ? "You are here" : place.locked ? "Locked · find three discoveries"
        : adjacent ? "Open doorway ↗" : place.visited ? "Visited · return by a connected room" : "Beyond your current room")
    );
    if (!button.disabled) button.addEventListener("click", () => act("travel", place.id));
    map.appendChild(button);
  }
}

function renderDiscoveries() {
  const shelf = $("world-discoveries");
  shelf.replaceChildren();
  for (const spec of [
    ["rule", "Entry inscription"],
    ["machine", "Paired machine"],
    ["seed", "Fresh Seed"],
    ["chronicle", "World chronicle"],
  ]) {
    const item = node("div", spec[1], "world-discovery");
    item.dataset.found = String(state.discoveries.includes(spec[0]));
    shelf.appendChild(item);
  }
  const completed = ["rule", "machine", "seed"].filter((id) => state.discoveries.includes(id)).length;
  $("world-discovery-count").textContent = completed + " / 3";
}

function renderHistory() {
  const history = $("world-history");
  history.replaceChildren();
  if (!state.history.length) {
    history.appendChild(node("p", "No local encounters recorded yet. Examine the entry inscription to begin."));
    return;
  }
  for (const event of state.history.slice(0, 12)) {
    const label = event.action === "travel" ? "Entered " +
      state.rooms.find((place) => place.id === event.room_id).title
      : "Examined " + state.rooms.find((place) => place.id === event.room_id).object.title;
    history.appendChild(node("p", label + " · " + new Date(event.created_at).toLocaleString()));
  }
}

function render() {
  const active = room();
  if (!active || !ROOM_IDS.includes(active.id)) throw new Error("Unknown local room");
  $("world-play").classList.remove("world-hidden");
  $("world-title").textContent = state.world.title;
  $("world-subtitle").textContent = "A fictional place assembled from one Machine, three Seeds, and your World rule.";
  $("world-scene").dataset.room = active.id;
  $("world-room-label").textContent = active.subtitle.toUpperCase();
  $("world-room-title").textContent = active.title;
  $("world-room-description").textContent = active.description;
  $("world-object-title").textContent = active.object.title;
  $("world-object-hint").textContent = active.object.hint;
  const examine = $("world-examine");
  examine.disabled = false;
  examine.textContent = active.object.discovered ? "Re-examine this object ↗" : "Examine this object ↗";
  const revelation = $("world-revelation");
  revelation.classList.toggle("world-hidden", !active.object.discovered);
  $("world-revelation-text").textContent = active.object.revelation || "";
  const origin = active.object.source;
  $("world-source-reference").textContent = origin.kind + " " + origin.id + " · SHA-256 " + origin.sha256;
  renderMap(active);
  renderDiscoveries();
  renderHistory();
}

async function start() {
  try {
    const params = new URLSearchParams(window.location.search);
    worldId = params.get("world");
    if (!worldId || !/^[a-f0-9]{32}$/.test(worldId)) {
      throw new Error("Choose Enter World on a World card in the House.");
    }
    const bootstrap = await api("/api/bootstrap");
    token = bootstrap.session_token;
    state = await api("/api/arg/worlds/" + worldId + "/play");
    render();
    $("world-examine").addEventListener("click", () => {
      const current = room();
      if (!OBJECT_IDS.includes(current.object.id)) return;
      act("examine", current.object.id);
    });
    message("World loaded. Your position and discoveries are preserved on this machine.");
  } catch (error) {
    $("world-title").textContent = "This door is not available.";
    $("world-subtitle").textContent = "Return to the House and select one of your Worlds.";
    message(error.message, true);
  }
}
start();
