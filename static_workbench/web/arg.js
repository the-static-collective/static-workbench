"use strict";
// STATIC-ARG-001: client UI for a bounded local, opt-in fictional composition shelf.
let sessionToken = "";
let current = { enrolled: false, artifacts: [], encounters: [] };
const byId = (id) => document.getElementById(id);

async function request(path, payload) {
  const options = { headers: { Accept: "application/json" } };
  if (payload !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.headers["x-workbench-session"] = sessionToken;
    options.body = JSON.stringify(payload);
  }
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Local request failed");
  return body;
}

function notice(text, error = false) {
  const node = byId("arg-status");
  node.textContent = text;
  node.className = error ? "arg-error" : "arg-success";
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function setOptions(id, artifacts, placeholder) {
  const select = byId(id);
  const previous = select.value;
  select.replaceChildren();
  const empty = element("option", placeholder);
  empty.value = "";
  select.appendChild(empty);
  artifacts.forEach((artifact) => {
    const option = element("option", artifact.snapshot.title + " · " + artifact.id.slice(0, 8));
    option.value = artifact.id;
    select.appendChild(option);
  });
  if (artifacts.some((a) => a.id === previous)) select.value = previous;
}

function updateWorldOptions() {
  const machine = current.artifacts.find((a) => a.id === byId("arg-world-machine").value && a.kind === "machine");
  const used = new Set(machine ? machine.snapshot.inputs.map((input) => input.id) : []);
  const available = current.artifacts.filter((a) => a.kind === "seed" && !used.has(a.id));
  setOptions("arg-world-seed", available, "Choose a fresh Seed");
  byId("arg-make-world").disabled = !machine || !available.length;
}

function updateOptions() {
  const seeds = current.artifacts.filter((a) => a.kind === "seed");
  const machines = current.artifacts.filter((a) => a.kind === "machine");
  setOptions("arg-first", seeds, "Choose the first Seed");
  setOptions("arg-second", seeds, "Choose a different Seed");
  byId("arg-make-machine").disabled = seeds.length < 2;
  setOptions("arg-world-machine", machines, "Choose a Machine");
  updateWorldOptions();
}

function artifactCard(artifact) {
  const card = element("article", undefined, "arg-item");
  card.appendChild(element("small", artifact.kind.toUpperCase() + " · " + artifact.created_at));
  card.appendChild(element("strong", artifact.snapshot.title));
  const copy = artifact.kind === "seed" ? artifact.snapshot.text
    : artifact.kind === "machine" ? artifact.snapshot.prompt
      : artifact.snapshot.play_rule;
  card.appendChild(element("pre", copy));
  const lineage = artifact.snapshot.inputs;
  if (lineage) {
    card.appendChild(element("small", "Inputs: " + lineage.map((x) => x.id.slice(0, 8) + "@" + x.sha256.slice(0, 12)).join(" + ")));
  } else {
    card.appendChild(element("small", "Human-entered local source"));
  }
  card.appendChild(element("code", "ID " + artifact.id + " · SHA-256 " + artifact.sha256));
  if (artifact.kind === "world") {
    const tip = element("p", "This World is a fictional sketch; its doors are manual navigation only.");
    card.appendChild(tip);
    for (const door of artifact.snapshot.doors) {
      const button = element("button", "Cross: " + door.id, "arg-door");
      button.type = "button";
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          const result = await request("/api/arg/cross", { world_id: artifact.id, door: door.id });
          // Destination is a server-selected fixed local path; never trust an arbitrary link.
          if (!["/", "/maddloop", "/machines"].includes(result.destination)) throw new Error("Unexpected destination");
          window.location.assign(result.destination);
        } catch (error) {
          notice(error.message, true);
          button.disabled = false;
        }
      });
      card.appendChild(button);
    }
  }
  return card;
}

function render() {
  byId("arg-loading").classList.add("arg-hidden");
  byId("arg-entry").classList.toggle("arg-hidden", current.enrolled);
  byId("arg-game").classList.toggle("arg-hidden", !current.enrolled);
  if (!current.enrolled) return;
  updateOptions();
  const artifacts = byId("arg-artifacts");
  artifacts.replaceChildren();
  if (!current.artifacts.length) artifacts.appendChild(element("p", "No Seeds yet. Make one above."));
  current.artifacts.forEach((item) => artifacts.appendChild(artifactCard(item)));
  const journal = byId("arg-encounters");
  journal.replaceChildren();
  if (!current.encounters.length) journal.appendChild(element("p", "No crossings yet. Your first World will open the next door."));
  current.encounters.forEach((item) => {
    const entry = element("div", undefined, "arg-item");
    entry.append(element("strong", item.door + " → " + item.destination),
      element("small", item.created_at + " · " + item.id),
      element("code", "Source " + item.source_id + "@" + item.source_sha256));
    journal.appendChild(entry);
  });
}

async function refresh() {
  current = await request("/api/arg/state");
  render();
}

function bindForm(id, route, payload, message) {
  byId(id).addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await request(route, payload());
      event.currentTarget.reset();
      await refresh();
      notice(message);
    } catch (error) {
      notice(error.message, true);
    } finally {
      if (id === "arg-seed-form") button.disabled = false;
      else updateOptions();
    }
  });
}

async function start() {
  try {
    const bootstrap = await request("/api/bootstrap");
    sessionToken = bootstrap.session_token;
    byId("arg-enter").addEventListener("click", async () => {
      byId("arg-enter").disabled = true;
      try {
        current = await request("/api/arg/enter", {});
        render();
        notice("Welcome to the House. Your local game shelf is ready.");
      } catch (error) {
        notice(error.message, true);
      } finally {
        byId("arg-enter").disabled = false;
      }
    });
    byId("arg-world-machine").addEventListener("change", updateWorldOptions);
    bindForm("arg-seed-form", "/api/arg/seeds", () => ({
      title: byId("arg-seed-title").value, text: byId("arg-seed-text").value
    }), "Seed preserved. Its source can be used in another composition.");
    bindForm("arg-machine-form", "/api/arg/machines", () => ({
      title: byId("arg-machine-title").value,
      first_id: byId("arg-first").value, second_id: byId("arg-second").value
    }), "Machine composed. Both source Seeds remain available.");
    bindForm("arg-world-form", "/api/arg/worlds", () => ({
      title: byId("arg-world-title").value,
      machine_id: byId("arg-world-machine").value, seed_id: byId("arg-world-seed").value,
      rule: byId("arg-world-rule").value
    }), "World preserved. Choose a doorway to continue the adventure.");
    await refresh();
  } catch (error) {
    byId("arg-loading").textContent = "The local House could not be reached.";
    notice(error.message, true);
  }
}
start();
