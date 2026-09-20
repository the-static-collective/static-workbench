/* ATTENTION-CROSSING-001 — explicit contextual human marks, never inferred. */
(() => {
  "use strict";
  const dimensions = ["joyful", "useful", "curiouser"];
  const names = {joyful:"☀ Joyful", useful:"✦ Useful", curiouser:"? Curiouser"};
  let tokenRequest = null;
  function session() {
    if (!tokenRequest) tokenRequest = fetch("/api/bootstrap").then(r => {
      if (!r.ok) throw Error("Workbench session unavailable");
      return r.json();
    }).then(data => data.session_token).catch(error => {
      tokenRequest = null; throw error;
    });
    return tokenRequest;
  }
  async function api(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw Error(data.detail || "Attention request failed");
    return data;
  }
  function mount(target, {kind, id, context = null}) {
    if (!target || !kind || !id || target.querySelector(":scope > .attention-bar")) return;
    const bar = document.createElement("div");
    bar.className = "attention-bar";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Attention crossing: " + kind + " " + id);
    const controls = document.createElement("div");
    controls.className = "attention-controls";
    const status = document.createElement("span");
    status.className = "attention-status";
    status.setAttribute("role", "status");
    const buttons = new Map();
    let current = null, selected = [], none = false, busy = true;
    function display() {
      buttons.forEach((button, key) => {
        const active = key === "none" ? none : selected.includes(key);
        button.disabled = busy;
        button.setAttribute("aria-pressed", String(active));
        button.classList.toggle("selected", active);
      });
    }
    async function read() {
      busy = true; status.textContent = "Loading attention…"; display();
      try {
        const query = new URLSearchParams({kind, target_id:id});
        const data = await api("/api/attention?" + query);
        current = data.current;
        selected = current ? current.dimensions.slice() : [];
        none = Boolean(current && current.explicit_none);
        status.textContent = current ? "Your declaration · revision " + current.id : "Not yet declared";
      } catch (error) {
        status.textContent = error.message;
      } finally { busy = false; display(); }
    }
    async function update(key) {
      const old = {current, selected:selected.slice(), none};
      if (key === "none") {
        selected = []; none = true;
      } else {
        selected = selected.includes(key) ? selected.filter(x => x !== key)
          : dimensions.filter(x => x === key || selected.includes(x));
        none = false;
      }
      busy = true; status.textContent = "Saving…"; display();
      try {
        const token = await session();
        const data = await api("/api/attention", {
          method:"POST",
          headers:{"Content-Type":"application/json", "x-workbench-session":token},
          body:JSON.stringify({kind, target_id:id, dimensions:selected, explicit_none:none,
                              expected_previous_id:old.current ? old.current.id : null, context})
        });
        current = data.current;
        status.textContent = "Your declaration · revision " + current.id;
      } catch (error) {
        current = old.current; selected = old.selected; none = old.none;
        status.textContent = error.message;
        if (error.message.includes("attention changed")) {
          await read(); return;
        }
      } finally { busy = false; display(); }
    }
    for (const key of [...dimensions, "none"]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "attention-button";
      button.textContent = key === "none" ? "None" : names[key];
      button.addEventListener("click", event => {
        event.stopPropagation();
        if (!busy) update(key);
      });
      buttons.set(key, button);
      controls.appendChild(button);
    }
    bar.append(controls, status);
    target.appendChild(bar);
    display();
    read();
  }
  function scan(root) {
    if (root.nodeType !== Node.ELEMENT_NODE) return;
    if (root.matches("[data-attention-kind][data-attention-id]")) {
      mount(root, {kind:root.dataset.attentionKind, id:root.dataset.attentionId});
    }
    root.querySelectorAll("[data-attention-kind][data-attention-id]").forEach(node => {
      mount(node, {kind:node.dataset.attentionKind, id:node.dataset.attentionId});
    });
  }
  const host = document.getElementById("workspace-body");
  if (host) {
    scan(host);
    new MutationObserver(changes => changes.forEach(change =>
      change.addedNodes.forEach(scan))).observe(host, {childList:true, subtree:true});
  }
  async function openShelf(dimension = "all") {
    const host = document.getElementById("workspace-body");
    if (!host) return;
    document.querySelectorAll(".nav-button").forEach(node =>
      node.classList.toggle("active", node.dataset.view === "attention"));
    document.getElementById("workspace-eyebrow").textContent = "Attention Crossing";
    document.getElementById("workspace-title").textContent = "What mattered to you";
    host.replaceChildren();
    const note = document.createElement("p");
    note.className = "muted";
    note.textContent = "Only your deliberate marks. Latest declaration first; no rankings.";
    const filter = document.createElement("select");
    filter.setAttribute("aria-label", "Filter attention by dimension");
    for (const key of ["all", ...dimensions]) {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = key === "all" ? "All declarations" : names[key];
      filter.appendChild(option);
    }
    filter.value = ["all",...dimensions].includes(dimension) ? dimension : "all";
    const transfer = document.createElement("section");
    transfer.className = "card attention-transfer";
    const transferTitle = document.createElement("h2");
    transferTitle.textContent = "Bring an attention crossing home";
    const help = document.createElement("p");
    help.className = "muted";
    help.textContent = "Paste one explicitly exported GOATnote or Static Live handoff. Review its self-reported source and fingerprint before importing a local copy.";
    const input = document.createElement("textarea");
    input.rows = 5; input.maxLength = 8192;
    input.placeholder = "Paste attention-crossing.handoff/v0.1 JSON";
    input.setAttribute("aria-label", "Attention handoff JSON");
    const review = document.createElement("button");
    review.type = "button"; review.textContent = "Preview exact handoff";
    const save = document.createElement("button");
    save.type = "button"; save.textContent = "Import reviewed copy"; save.disabled = true;
    const feedback = document.createElement("div");
    feedback.setAttribute("role", "status"); feedback.className = "muted tiny";
    let reviewed = null;
    input.addEventListener("input", () => {reviewed = null;save.disabled = true;feedback.textContent = "Preview required after any change.";});
    review.addEventListener("click", async () => {
      reviewed = null;save.disabled = true;
      try {
        const token = await session();
        const body = await api("/api/attention/import/preview", {
          method:"POST", headers:{"Content-Type":"application/json","x-workbench-session":token},
          body:JSON.stringify({raw_json:input.value})
        });
        reviewed = {raw:input.value, sha:body.raw_sha256};
        const h = body.handoff;
        feedback.textContent = h.source_app + " · " + h.source_locator + " · " +
          (h.explicit_none ? "explicit none" : h.dimensions.join(" / ") || "unmarked") +
          " · declared " + h.source_recorded_at + " · SHA-256 " + body.raw_sha256 +
          " · self-reported source; not independently verified.";
        save.disabled = false;
      } catch(error) {feedback.textContent = error.message;}
    });
    save.addEventListener("click", async () => {
      if (!reviewed || reviewed.raw !== input.value) {save.disabled = true;return;}
      save.disabled = true;
      try {
        const token = await session();
        const body = await api("/api/attention/import/save", {
          method:"POST",headers:{"Content-Type":"application/json","x-workbench-session":token},
          body:JSON.stringify({raw_json:reviewed.raw,expected_sha256:reviewed.sha})
        });
        feedback.textContent = body.duplicate ? "Already imported as local receipt #" + body.import.import_id :
          "Imported as local receipt #" + body.import.import_id + ". Source-owned declaration remains separate.";
        reviewed = null;
        await draw();
      } catch(error) {feedback.textContent = error.message;}
    });
    transfer.append(transferTitle,help,input,review,save,feedback);
    const list = document.createElement("div");
    list.className = "attention-shelf";
    host.append(note,transfer,filter,list);
    async function draw() {
      list.textContent = "Loading local attention shelf…";
      try {
        const feed = await api("/api/attention/feed?" +
          new URLSearchParams({dimension:filter.value, limit:"100"}));
        list.replaceChildren();
        if (!feed.entries.length) {
          const empty = document.createElement("p");
          empty.className = "muted";
          empty.textContent = "No Workbench-originated declarations in this filter.";
          list.appendChild(empty);
        }
        const localHeading=document.createElement("h2");
        localHeading.textContent="Workbench-originated crossings";
        list.appendChild(localHeading);
        for (const record of feed.entries) {
          const card = document.createElement("article");
          card.className = "card attention-shelf-card";
          const heading = document.createElement("strong");
          heading.textContent = record.context?.excerpt || record.kind + " · " + record.target_id;
          const detail = document.createElement("p");
          detail.className = "muted tiny";
          detail.textContent = new Date(record.created_at).toLocaleString() +
            " · " + (record.explicit_none ? "Explicitly none" :
            record.dimensions.length ? record.dimensions.join(" / ") : "Unmarked revision");
          card.append(heading, detail);
          list.appendChild(card);
          mount(card, {kind:record.kind, id:record.target_id, context:record.context});
        }
        const imported = await api("/api/attention/imports?" +
          new URLSearchParams({dimension:filter.value,limit:"100"}));
        const importedHeading = document.createElement("h2");
        importedHeading.textContent = "Returned crossings · source-owned, imported copies";
        list.appendChild(importedHeading);
        if (!imported.entries.length) {
          const empty = document.createElement("p");empty.className = "muted";
          empty.textContent = "No reviewed external handoffs for this filter.";
          list.appendChild(empty);
        }
        for (const entry of imported.entries) {
          const h=entry.handoff;
          const card=document.createElement("article");
          card.className="card attention-shelf-card";
          const heading=document.createElement("strong");
          heading.textContent=h.label;
          const detail=document.createElement("p");detail.className="muted tiny";
          detail.textContent=h.source_app+" · "+h.source_locator+" · declared "+h.source_recorded_at+
            " · imported "+new Date(entry.imported_at).toLocaleString();
          const mark=document.createElement("p");mark.className="muted";
          mark.textContent=h.explicit_none?"Explicitly none":h.dimensions.join(" / ")||"Unmarked revision";
          const boundary=document.createElement("p");boundary.className="muted tiny";
          boundary.textContent="Self-reported export · Workbench import #"+entry.import_id+
            " · NOT a Workbench-originated declaration or verified source observation.";
          card.append(heading,detail,mark,boundary);list.appendChild(card);
        }
      } catch (error) { list.textContent = error.message; }
    }
    filter.addEventListener("change", draw);
    await draw();
  }
  // User-initiated passage capture within a declared Workbench context only.
  // Selecting text does not persist it or send a request.
  const capture = document.createElement("button");
  capture.type = "button";
  capture.className = "attention-capture-button";
  capture.textContent = "Mark selected passage";
  capture.hidden = true;
  document.body.appendChild(capture);
  const panel = document.createElement("aside");
  panel.className = "attention-selection-panel";
  panel.hidden = true;
  panel.setAttribute("aria-label", "Selected passage attention crossing");
  document.body.appendChild(panel);
  let snapshot = null;
  function offerSelection() {
    capture.hidden = true;
    snapshot = null;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount !== 1) return;
    const range = selection.getRangeAt(0);
    const start = range.startContainer.nodeType === Node.ELEMENT_NODE ?
      range.startContainer : range.startContainer.parentElement;
    const end = range.endContainer.nodeType === Node.ELEMENT_NODE ?
      range.endContainer : range.endContainer.parentElement;
    if (!start || !end || !host.contains(start) || !host.contains(end)) return;
    if (start.closest(".attention-bar,.attention-shelf,input,textarea,[contenteditable]")) return;
    const source = start.closest("[data-attention-kind][data-attention-id]");
    if (!source || source !== end.closest("[data-attention-kind][data-attention-id]")) return;
    const quote = selection.toString().trim();
    if (!quote || quote.length > 512 || /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(quote)) return;
    snapshot = {kind:source.dataset.attentionKind, id:source.dataset.attentionId, quote};
    capture.hidden = false;
  }
  host?.addEventListener("mouseup", offerSelection);
  host?.addEventListener("keyup", offerSelection);
  capture.addEventListener("click", async () => {
    const value = snapshot;
    snapshot = null;
    capture.hidden = true;
    if (!value) return;
    panel.replaceChildren();
    panel.hidden = false;
    const label = document.createElement("p");
    label.className = "muted tiny";
    label.textContent = "Selected by you within " + value.kind + ":" + value.id;
    const excerpt = document.createElement("blockquote");
    excerpt.textContent = value.quote;
    const close = document.createElement("button");
    close.type = "button";
    close.className = "attention-button";
    close.textContent = "Close";
    close.addEventListener("click", () => { panel.hidden = true; panel.replaceChildren(); });
    panel.append(label, excerpt, close);
    try {
      const digest = async text => Array.from(new Uint8Array(
        await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text))),
        n => n.toString(16).padStart(2,"0")).join("");
      const quoteHash = await digest(value.quote);
      // A repeated exact quote in the same source is one target in this prototype.
      const targetId = await digest(value.kind + ":" + value.id + ":" + quoteHash);
      mount(panel, {kind:"selection", id:targetId, context:{
        scope:"selected-passage", source_kind:value.kind, source_id:value.id,
        excerpt:value.quote.slice(0,160), quote_sha256:quoteHash}});
    } catch (error) {
      const failure = document.createElement("p");
      failure.textContent = error.message;
      panel.appendChild(failure);
    }
  });
  window.HumanValueBar = Object.freeze({mount, openShelf});
})();
