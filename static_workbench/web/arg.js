"use strict";
// STATIC-ARG-001: client UI for a bounded local, opt-in fictional composition shelf.
let sessionToken = "";
let current = { enrolled: false, artifacts: [], encounters: [] };
let artifactFilter = "all";
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
  card.dataset.kind = artifact.kind;
  card.appendChild(element("small", artifact.kind.toUpperCase() + " · " + new Date(artifact.created_at).toLocaleString()));
  card.appendChild(element("strong", artifact.snapshot.title));
  const copy = artifact.kind === "seed" ? artifact.snapshot.text
    : artifact.kind === "machine" ? artifact.snapshot.prompt
      : artifact.snapshot.play_rule;
  card.appendChild(element("pre", copy));
  const lineage = artifact.snapshot.inputs;
  const provenance = element("details");
  provenance.appendChild(element("summary", "Inspect source lineage"));
  if (lineage) {
    provenance.appendChild(element("small", "Inputs: " + lineage.map((x) => x.id.slice(0, 8) + "@" + x.sha256.slice(0, 12)).join(" + ")));
  } else {
    provenance.appendChild(element("small", "Human-entered local source"));
  }
  provenance.appendChild(element("code", "ID " + artifact.id + " · SHA-256 " + artifact.sha256));
  card.appendChild(provenance);
  if (artifact.kind === "world") {
    const enter = element("a", "Enter World ↗", "arg-world-link");
    enter.href = "/arg/world?world=" + encodeURIComponent(artifact.id);
    card.appendChild(enter);
    const tip = element("p", "Explore source-linked rooms or use an ordinary local Workbench doorway below.");
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

function focusStage(targetId) {
  const target = byId(targetId);
  if (!target) return;
  target.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  const focusable = target.matches("form") ? target.querySelector("input,select,textarea") : target.querySelector("button, a, input");
  if (focusable) focusable.focus({ preventScroll: true });
}

function updateJourney() {
  const seeds = current.artifacts.filter((a) => a.kind === "seed").length;
  const machines = current.artifacts.filter((a) => a.kind === "machine").length;
  const worlds = current.artifacts.filter((a) => a.kind === "world").length;
  const visits = current.encounters.length;
  const steps = [
    ["seed", seeds > 0 ? "done" : "ready", seeds + " collected"],
    ["machine", machines > 0 ? "done" : seeds >= 2 ? "ready" : "locked", machines + " composed"],
    ["world", worlds > 0 ? "done" : machines > 0 && seeds >= 3 ? "ready" : "locked", worlds + " created"],
    ["return", visits > 0 ? "done" : worlds > 0 ? "ready" : "locked", visits + " crossings"],
  ];
  for (const [id, status, count] of steps) {
    byId("arg-step-" + id).dataset.state = status;
    byId("arg-count-" + (id === "seed" ? "seeds" : id === "machine" ? "machines" : id === "world" ? "worlds" : "returns")).textContent = count;
    if (id !== "return") byId("arg-panel-" + id).dataset.stage = status;
  }
  byId("arg-seed-hint").textContent = seeds < 2 ? "Plant " + (2 - seeds) + " more Seed" + (2 - seeds === 1 ? "" : "s") + " to compose a Machine." : "Seeds ready. Compose two or keep planting.";
  byId("arg-machine-hint").textContent = seeds < 2 ? "Two distinct Seeds are needed to compose." : "Choose any two distinct Seeds. The originals remain intact.";
  byId("arg-world-hint").textContent = machines === 0 ? "Compose a Machine first." : "Choose a Machine and a fresh Seed not used by it.";
  const next = worlds > 0
    ? ["Explore your World", "Cross a doorway, or return to make another composition.", "arg-collection"]
    : machines > 0 && seeds >= 3
      ? ["Shape your first World", "Give your Machine a fresh Seed and a playable rule.", "arg-world-form"]
      : machines > 0
        ? ["Plant a fresh Seed", "Your Machine needs one more Seed to become a World.", "arg-seed-form"]
        : seeds >= 2
          ? ["Compose your first Machine", "Pair two Seeds to create a reusable creative prompt.", "arg-machine-form"]
          : ["Plant your next Seed", "Start with one small idea. Nothing needs to be perfect.", "arg-seed-form"];
  byId("arg-next-title").textContent = "Your next move: " + next[0];
  byId("arg-next-detail").textContent = next[1];
  byId("arg-next-button").dataset.target = next[2];
  byId("arg-artifact-total").textContent = current.artifacts.length + " artifacts";
}

function renderArtifacts() {
  const artifacts = byId("arg-artifacts");
  artifacts.replaceChildren();
  const visible = current.artifacts.filter((item) => artifactFilter === "all" || item.kind === artifactFilter);
  if (!visible.length) artifacts.appendChild(element("p", current.artifacts.length ? "No artifacts of this kind yet." : "No Seeds yet. Make one above."));
  visible.forEach((item) => artifacts.appendChild(artifactCard(item)));
  document.querySelectorAll(".arg-filter button").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.filter === artifactFilter));
  });
}

function render() {
  byId("arg-loading").classList.add("arg-hidden");
  byId("arg-entry").classList.toggle("arg-hidden", current.enrolled);
  byId("arg-game").classList.toggle("arg-hidden", !current.enrolled);
  if (!current.enrolled) return;
  updateOptions();
  updateJourney();
  renderArtifacts();
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
    document.querySelectorAll(".arg-milestone").forEach((button) => {
      button.addEventListener("click", () => focusStage(button.dataset.target));
    });
    byId("arg-next-button").addEventListener("click", () => focusStage(byId("arg-next-button").dataset.target));
    document.querySelectorAll(".arg-filter button").forEach((button) => {
      button.addEventListener("click", () => {
        artifactFilter = button.dataset.filter;
        renderArtifacts();
      });
    });
    byId("arg-first").addEventListener("change", () => {
      if (byId("arg-first").value && byId("arg-first").value === byId("arg-second").value) {
        byId("arg-second").value = "";
      }
    });
    byId("arg-second").addEventListener("change", () => {
      if (byId("arg-second").value && byId("arg-second").value === byId("arg-first").value) {
        byId("arg-second").value = "";
        notice("Choose a second, different Seed.", true);
      }
    });
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
