"use strict";
// WEBZ-RELATTE-002: a material-carry instrument deliberately separate from
// no-carry scene navigation. Browser JS never signs or decides destination law.
const mode = document.body?.dataset?.webzWorld;
const KINDS = new Set(["fruit", "spore"]);
const $ = (id) => document.getElementById(id);

async function getJson(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: {Accept: "application/json", ...(options.headers || {})},
    ...options,
  });
  let body = null;
  try { body = await response.json(); }
  catch (_) { /* non-JSON error becomes a visible refusal */ }
  if (!response.ok) {
    throw new Error(typeof body?.detail === "string"
      ? body.detail : "The local reLATTE carrier or receiver is unavailable.");
  }
  return body;
}

function span(text, className = "") {
  const el = document.createElement("span");
  el.className = className;
  el.textContent = String(text);
  return el;
}
function para(text, className = "") {
  const el = document.createElement("p");
  el.className = className;
  el.textContent = String(text);
  return el;
}

function bindSanctuary() {
  const select = $("webz-parcel-kind");
  const inspect = $("webz-parcel-inspect");
  const preview = $("webz-parcel-preview");
  const consent = $("webz-parcel-confirm");
  const send = $("webz-parcel-send");
  const status = $("webz-parcel-status");
  let selected = null;
  let generation = 0;

  function reset() {
    selected = null;
    generation += 1;
    consent.checked = false;
    consent.disabled = true;
    send.disabled = true;
    preview.hidden = true;
    preview.textContent = "";
    status.textContent = "No material offered. Inspect one exact first-party fixture before sending.";
  }
  select.addEventListener("change", reset);
  consent.addEventListener("change", () => {
    send.disabled = !selected || !consent.checked;
  });
  inspect.addEventListener("click", async () => {
    reset();
    const mine = generation;
    const kind = select.value;
    if (!KINDS.has(kind)) return;
    inspect.disabled = true;
    status.textContent = "Reading the immutable fictional parcel proposal…";
    try {
      const item = await getJson("/api/webz/parcels/" + kind + "/preview");
      if (mine !== generation) return;
      if (item.schema !== "workbench.webz-parcel-preview/v0" ||
          item.kind !== kind ||
          typeof item.artifact_sha256 !== "string" ||
          !/^[a-f0-9]{64}$/.test(item.artifact_sha256) ||
          item.destination_world_id !== "webz:the-static-collective/orchard-022100" ||
          !["HOLD", "REFUSE"].includes(item.policy)) {
        throw new Error("The first-party parcel declaration was not recognized.");
      }
      selected = item;
      preview.hidden = false;
      preview.textContent =
        "ARTIFACT · " + item.title + "\n" +
        "SOURCE · " + item.source_world_id + "\n" +
        "DESTINATION · " + item.destination_world_id + "\n" +
        "KIND · " + item.artifact_kind + "\n" +
        "SHA-256 · " + item.artifact_sha256 + "\n" +
        "BYTES · " + item.artifact_bytes + "\n" +
        "ORCHARD POLICY · " + item.policy + " (not ADMIT)\n" +
        "CARRIER · pinned reLATTE / exact local bytes";
      consent.disabled = false;
      status.textContent =
        "PREVIEW ONLY. No payload, signature, receipt, or admission has been created. " +
        "Select the consent box to authorize this exact fixture.";
    } catch (error) {
      if (mine === generation) status.textContent = "UNRESOLVED PREVIEW · " + error.message;
    } finally {
      inspect.disabled = false;
    }
  });

  send.addEventListener("click", async () => {
    if (!selected || !consent.checked || send.disabled ||
        selected.kind !== select.value || !KINDS.has(selected.kind)) return;
    // An explicit second action; no implicit background retries.
    const offering = selected;
    send.disabled = true;
    inspect.disabled = true;
    consent.disabled = true;
    status.textContent = "Offering the exact fictional fixture to the pinned reLATTE receiver…";
    try {
      const bootstrap = await getJson("/api/bootstrap");
      if (!bootstrap || typeof bootstrap.session_token !== "string") {
        throw new Error("Workbench operator session is unavailable.");
      }
      const outcome = await getJson(
        "/api/webz/parcels/" + offering.kind + "/send",
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "x-workbench-session": bootstrap.session_token,
          },
          body: JSON.stringify({
            expected_sha256: offering.artifact_sha256,
            confirmation: "SEND_TO_ORCHARD",
          }),
        },
      );
      if (outcome.schema !== "workbench.webz-parcel-result/v0" ||
          outcome.artifact_sha256 !== offering.artifact_sha256 ||
          outcome.admitted !== false ||
          outcome.receiver_disposition !== offering.policy) {
        throw new Error("The returned receipt did not match the selected parcel.");
      }
      status.textContent =
        "ORCHARD RECEIVER: " + outcome.status +
        "\nRECEIVE: " + outcome.receive_receipt_id +
        "\nDISPOSITION: " + outcome.disposition_receipt_id +
        "\nCROSSING: " + outcome.crossing_id +
        "\nADMITTED: NO. Visit the Orchard to inspect its read-only signed proof.";
    } catch (error) {
      status.textContent =
        "NO CONFIRMED MATERIAL CROSSING · " + error.message +
        "\nAn uncertain outcome is not a reason for automatic retry. " +
        "Inspect local state before trying again.";
    } finally {
      selected = null;
      consent.checked = false;
      consent.disabled = true;
      inspect.disabled = false;
      send.disabled = true;
    }
  });
}

function bindOrchard() {
  const shelf = $("webz-parcel-inbox");
  const refresh = $("webz-parcel-refresh");
  const proof = $("webz-parcel-proof");
  async function renderInbox() {
    shelf.replaceChildren();
    proof.hidden = true;
    proof.textContent = "";
    refresh.disabled = true;
    try {
      const data = await getJson("/api/webz/parcels/inbox");
      if (!data || !Array.isArray(data.parcels)) throw new Error("Invalid receiver view.");
      if (data.parcels.length === 0) {
        shelf.appendChild(para(
          "NO RECEIVER RECORD YET · No fictional parcel is present. Simply entering this world does not deliver or admit material.",
          "webz-parcel-empty",
        ));
      }
      for (const record of data.parcels) {
        if (!KINDS.has(record.kind)) continue;
        const card = document.createElement("article");
        card.className = "webz-parcel-receipt";
        card.append(
          span(record.kind.toUpperCase() + " · " + record.status, "webz-receipt-kind"),
          para("DECISION · " + record.receiver_disposition + " · NOT ADMITTED"),
          para("SHA-256 · " + record.artifact_sha256, "webz-mono"),
          para("CROSSING · " + record.crossing_id, "webz-mono"),
          para("RECEIVE · " + record.receive_receipt_id, "webz-mono"),
          para("DISPOSITION · " + record.disposition_receipt_id, "webz-mono"),
        );
        const inspectProof = document.createElement("button");
        inspectProof.type = "button";
        inspectProof.className = "webz-button webz-quiet webz-small";
        inspectProof.textContent = "Inspect public signed evidence ↗";
        inspectProof.addEventListener("click", async () => {
          proof.hidden = false;
          proof.textContent = "Loading the owner's public signature evidence…";
          try {
            const packet = await getJson("/api/webz/parcels/" + record.kind + "/proof");
            if (packet.schema !== "workbench.webz-parcel-proof/v0") {
              throw new Error("Unknown proof schema.");
            }
            proof.textContent = JSON.stringify(packet, null, 2);
          } catch (error) {
            proof.textContent = "PROOF UNAVAILABLE · " + error.message;
          }
        });
        card.appendChild(inspectProof);
        shelf.appendChild(card);
      }
    } catch (error) {
      shelf.replaceChildren(para(
        "RECEIVER EVIDENCE UNAVAILABLE · " + error.message +
        ". No confirmed state has been silently invented.",
        "webz-parcel-error",
      ));
    } finally {
      refresh.disabled = false;
    }
  }
  refresh.addEventListener("click", renderInbox);
  // A read-only inbox GET is safe on world entry; there is never an automatic SEND.
  renderInbox();
}
if (mode === "sanctuary" && $("webz-parcel-send")) bindSanctuary();
if (mode === "orchard" && $("webz-parcel-inbox")) bindOrchard();
