import {readVoyage, exportVoyage, eraseVoyage} from "./webz-storage.mjs";
"use strict";
// A Workbench-native textual resolver, not an OS/browser protocol registration.
const $ = (id) => document.getElementById(id);
const form = $("webz-form");
const input = $("webz-address");
const resolveButton = $("webz-resolve");
const enterButton = $("webz-enter");
const result = $("webz-result");
const ALLOWED_WORLDS = new Map([
  ["/webz/world/sanctuary", "webz:the-static-collective/sanctuary"],
  ["/webz/world/orchard", "webz:the-static-collective/orchard-022100"],
]);
let selection = null;
let requestNumber = 0;

function clearSelection() {
  selection = null;
  enterButton.disabled = true;
  enterButton.hidden = true;
  requestNumber += 1;
}

function showLine(message) {
  result.textContent = message;
}
input.addEventListener("input", () => {
  clearSelection();
  showLine("Address changed. Resolve again before entering.");
});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearSelection();
  const mine = requestNumber;
  const address = input.value;
  showLine("Resolving the local world declaration…");
  resolveButton.disabled = true;
  try {
    const response = await fetch("/api/webz/resolve?address=" + encodeURIComponent(address), {
      headers: {Accept: "application/json"},
    });
    if (!response.ok) throw new Error("The world registry is unavailable.");
    const decision = await response.json();
    if (mine !== requestNumber) return;
    if (decision.status === "resolved" &&
        ALLOWED_WORLDS.get(decision.entry_route) === decision.world_id &&
        decision.typed_address === address) {
      selection = decision;
      showLine(decision.title + "\n" + decision.world_id + "\nRevision: " +
        decision.manifest_revision + " · " + decision.source +
        "\nNo carry. Nothing has been entered or admitted.");
      enterButton.hidden = false;
      enterButton.disabled = false;
    } else if (decision.status === "unresolved") {
      showLine("UNRESOLVED · No installed world answers this address. You have not departed.");
    } else {
      showLine("INVALID ADDRESS · Expected webz::namespace/path, lowercase ASCII only.");
    }
  } catch (error) {
    if (mine === requestNumber) showLine("RESOLUTION UNAVAILABLE · " + error.message);
  } finally {
    resolveButton.disabled = false;
  }
});
enterButton.addEventListener("click", () => {
  if (!selection || enterButton.disabled || ALLOWED_WORLDS.get(selection.entry_route) !== selection.world_id) return;
  // Only a distinct human click here performs a navigation.
  window.location.assign(selection.entry_route);
});
for (const card of document.querySelectorAll("[data-webz-address]")) {
  card.addEventListener("click", () => {
    input.value = card.dataset.webzAddress;
    clearSelection();
    input.focus();
    showLine("Address selected. Resolve it before choosing to enter.");
  });
}

const localStatus = $("webz-recording-status");
const localExport = $("webz-export-voyage");
const localErase = $("webz-erase-voyage");
function localStorageSafely() {
  try { return window.localStorage; }
  catch (_) {
    return {getItem(){throw new Error("blocked");},
      setItem(){throw new Error("blocked");},removeItem(){throw new Error("blocked");}};
  }
}
function renderLocalVoyage() {
  const current = readVoyage(localStorageSafely());
  const valid = current.status === "recording" || current.status === "paused";
  localExport.disabled = !(valid || current.status === "corrupt");
  localErase.disabled = current.status === "off" || current.status === "unavailable";
  const count = current.record?.events?.length ?? 0;
  localStatus.textContent = valid
    ? "LOCAL / " + current.status + " / " + count + " navigation events · not a STORYSHIP or reLATTE receipt."
    : current.status === "corrupt"
      ? "CORRUPT · Export raw history before choosing Erase. Nothing was silently repaired."
      : current.status === "unavailable"
        ? "Browser storage unavailable; world navigation remains usable."
        : "Recording is off. Begin a voyage after entering a world.";
}
function downloadLocal(text, filename, mime) {
  const url = URL.createObjectURL(new Blob([text], {type:mime}));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
localExport.addEventListener("click", () => {
  try {
    const current = readVoyage(localStorageSafely());
    if (current.status === "corrupt") {
      const raw = localStorageSafely().getItem("webz.voyage-local.v0");
      if (raw === null) throw new Error("no raw history");
      downloadLocal(raw,"webz-raw-local-recovery.txt","text/plain");
    } else {
      downloadLocal(exportVoyage(localStorageSafely()),"webz-voyage-local-v0.json","application/json");
    }
    renderLocalVoyage();
  } catch (_) {
    localStatus.textContent = "Export unavailable; your original local history was not changed.";
  }
});
localErase.addEventListener("click", () => {
  if (!window.confirm("Erase the browser-local webZ voyage? Export first to keep it.")) return;
  const result=eraseVoyage(localStorageSafely());
  renderLocalVoyage();
  if (result.status === "unavailable") localStatus.textContent = result.error;
});
renderLocalVoyage();
