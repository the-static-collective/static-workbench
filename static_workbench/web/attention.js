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
  function mount(target, {kind, id}) {
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
                              expected_previous_id:old.current ? old.current.id : null})
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
    const list = document.createElement("div");
    list.className = "attention-shelf";
    host.append(note, filter, list);
    async function draw() {
      list.textContent = "Loading local attention shelf…";
      try {
        const feed = await api("/api/attention/feed?" +
          new URLSearchParams({dimension:filter.value, limit:"100"}));
        list.replaceChildren();
        if (!feed.entries.length) {
          const empty = document.createElement("p");
          empty.className = "muted";
          empty.textContent = "No current declarations in this filter.";
          list.appendChild(empty);
        }
        for (const record of feed.entries) {
          const card = document.createElement("article");
          card.className = "card attention-shelf-card";
          const heading = document.createElement("strong");
          heading.textContent = record.kind + " · " + record.target_id;
          const detail = document.createElement("p");
          detail.className = "muted tiny";
          detail.textContent = new Date(record.created_at).toLocaleString() +
            " · " + (record.explicit_none ? "Explicitly none" :
            record.dimensions.length ? record.dimensions.join(" / ") : "Unmarked revision");
          card.append(heading, detail);
          list.appendChild(card);
          mount(card, {kind:record.kind, id:record.target_id});
        }
      } catch (error) { list.textContent = error.message; }
    }
    filter.addEventListener("change", draw);
    await draw();
  }
  window.HumanValueBar = Object.freeze({mount, openShelf});
})();
