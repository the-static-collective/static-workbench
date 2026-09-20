const state = { bootstrap: null, machine: null, repos: [], house: null, view: 'house', creator: null, broadcast: null, apertureHistory: [], apertureCurrent: null, apertureParentId: null };
const APERTURE_BOUNDARY = 'possible meaning != intended meaning';

const $ = (selector) => document.querySelector(selector);
const workspaceBody = $('#workspace-body');

async function api(path, options = {}) {
  const headers = { 'Accept': 'application/json', ...(options.headers || {}) };
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const response = await fetch(path, { ...options, headers });
  let body = null;
  try { body = await response.json(); } catch (_) { /* ignored */ }
  if (!response.ok) throw new Error(body?.detail || `${response.status} ${response.statusText}`);
  return body;
}

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function formatBytes(value) {
  if (value === null || value === undefined) return 'unavailable';
  const units = ['B','KiB','MiB','GiB','TiB'];
  let n = Number(value), i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i += 1; }
  return `${n >= 10 || i === 0 ? n.toFixed(0) : n.toFixed(1)} ${units[i]}`;
}
function timeLabel(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.valueOf()) ? iso : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
function showError(error) {
  clear(workspaceBody);
  const box = el('div', 'notice error', error.message || String(error));
  workspaceBody.appendChild(box);
}
function meter(percent) {
  const outer = el('div', 'meter');
  const inner = el('span');
  inner.style.width = `${Math.max(0, Math.min(100, Number(percent) || 0))}%`;
  outer.appendChild(inner);
  return outer;
}
function metricCard(label, value, percent = null) {
  const card = el('article', 'card');
  card.append(el('div', 'metric-label', label), el('div', 'metric-value', value));
  if (percent !== null) card.appendChild(meter(percent));
  return card;
}
function setWorkspace(eyebrow, title) {
  $('#workspace-eyebrow').textContent = eyebrow;
  $('#workspace-title').textContent = title;
}
function syncNav(view) {
  document.querySelectorAll('.nav-button').forEach(node => node.classList.toggle('active', node.dataset.view === view));
}
function repoHealth(repo) {
  if (repo.detached) return ['detached', 'warn'];
  if ((repo.behind || 0) > 0) return [`behind ${repo.behind}`, 'warn'];
  if ((repo.ahead || 0) > 0) return [`ahead ${repo.ahead}`, 'info'];
  if (repo.dirty) return ['dirty', 'warn'];
  return ['clean', 'good'];
}
function stackLabel(repo) {
  return repo.stacks && repo.stacks.length ? repo.stacks.join(' + ') : 'unclassified';
}

function isSafeBroadcastUrl(value) {
  if (typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' && url.hostname === '127.0.0.1'
      && url.port !== '' && url.pathname === '/' && url.search === '' && url.hash === ''
      && url.username === '' && url.password === ''
      && value === `http://127.0.0.1:${url.port}/`;
  } catch (_) { return false; }
}

function renderHouse() {
  state.view = 'house'; syncNav('house');
  setWorkspace('House', 'The local habitat');
  clear(workspaceBody);
  const house = state.house;
  if (!house) { workspaceBody.appendChild(el('div', 'empty-state', 'House inventory unavailable.')); return; }

  const hero = el('section', 'house-hero card');
  const copy = el('div');
  copy.append(el('div', 'eyebrow', 'LOCAL / LOOPBACK / ATTRIBUTABLE'), el('h2', 'house-title', 'The house is awake.'));
  copy.appendChild(el('p', 'muted', 'Downloaded repositories become visible organs here. Presence is discovered automatically; readiness, compatibility, and authority remain separate facts.'));
  const law = el('div', 'law-strip');
  house.laws.forEach(item => law.appendChild(el('span', 'law-chip', item)));
  copy.appendChild(law);
  const pulse = el('div', 'house-pulse');
  pulse.append(el('div', 'pulse-number', String(house.summary.repos)), el('div', 'muted tiny', 'repos visible'));
  hero.append(copy, pulse);
  workspaceBody.appendChild(hero);

  const summary = el('div', 'metric-grid house-metrics');
  summary.append(
    metricCard('Core organs', `${house.summary.core_organs_present}/${house.summary.core_organs_total}`),
    metricCard('Dirty trees', String(house.summary.dirty)),
    metricCard('Diverged', String(house.summary.diverged)),
    metricCard('Detached', String(house.summary.detached))
  );
  workspaceBody.appendChild(summary);

  const ready = el('section', 'house-section');
  ready.appendChild(el('div', 'section-heading', 'READY NOW'));
  const actions = el('div', 'action-grid');
  const inspect = el('button', 'action-card');
  inspect.append(el('strong', '', 'Inventory the body'), el('span', 'muted', 'Inspect every discovered repository, branch, stack marker, and worktree state.'));
  inspect.addEventListener('click', renderRepos);
  const terminal = el('button', 'action-card');
  terminal.append(el('strong', '', 'Open HumanTerminal'), el('span', 'muted', 'Preserve a raw carrier and bounded sense-field cut without promoting meaning to authority.'));
  terminal.addEventListener('click', renderHumanTerminal);
  const creator = el('button', 'action-card');
  creator.append(el('strong', '', 'Open Creator Desk'), el('span', 'muted', 'Search a chosen local source and carry its exact provenance into a draft or research brief.'));
  creator.addEventListener('click', renderCreatorDesk);
  const nativeMaxhinal = el('button', 'action-card');
  nativeMaxhinal.append(el('strong', '', 'Open HOUSE Maxhinal'),
    el('span', 'muted', 'Spin explicitly selected local files and source packs into bounded creative projections with attributable receipts.'));
  nativeMaxhinal.addEventListener('click', renderNativeMaxhinal);
  const dogramLab = el('button', 'action-card');
  dogramLab.append(el('strong', '', 'Open Dogram Lab'),
    el('span', 'muted', 'Compare two committed Python dependency graphs with a pinned local Dogram research calculation.'));
  dogramLab.addEventListener('click', renderDogramImpactDesk);
  actions.append(inspect, terminal, creator, nativeMaxhinal, dogramLab);
  const staticLive = house.organs.find(organ => organ.id === 'static-live' && organ.present);
  if (staticLive) {
    const live = el('button', 'action-card');
    live.append(el('strong', '', 'Inspect first-heartbeat lane'), el('span', 'muted', 'Static Live is present. Open its exact local checkout before running any project-owned commands.'));
    live.addEventListener('click', () => renderRepoDetail(staticLive.repo));
    actions.appendChild(live);
    const door = state.broadcast;
    const broadcast = el('article', 'action-card broadcast-door');
    broadcast.appendChild(el('strong', '', 'Static Broadcast / local operator door'));
    if (door?.connection === 'reachable' && isSafeBroadcastUrl(door.open_url)) {
      broadcast.append(
        el('span', 'muted', `${door.event.title} · ${door.broadcast_state}`),
        el('span', 'muted tiny', `Recording: ${door.recording ? 'active' : 'off'} · Streaming: ${door.stream ? 'live' : 'off'} · Self-reported local service, not an identity proof.`)
      );
      const open = el('a', 'action-button', 'Open Static Broadcast');
      open.href = door.open_url; open.target = '_blank'; open.rel = 'noopener noreferrer';
      open.setAttribute('aria-label', 'Open the configured local Static Broadcast operator console');
      broadcast.appendChild(open);
    } else {
      const labels = {
        unconfigured: 'Not configured. Set broadcast_port in the local HOUSE config; checkout presence is not running-service readiness.',
        offline_or_incompatible: 'No compatible local console is responding on the declared port.',
        unrecognized_service: 'Another service or incompatible console answered. Opening is refused.',
        invalid_configuration: 'Invalid local broadcast port. Correct the HOUSE configuration.',
      };
      broadcast.appendChild(el('span', 'muted', labels[door?.connection] || 'Checking local broadcast connection…'));
    }
    actions.appendChild(broadcast);
  }
  ready.appendChild(actions);
  workspaceBody.appendChild(ready);

  const organs = el('section', 'house-section');
  organs.appendChild(el('div', 'section-heading', 'ORGANS'));
  const grid = el('div', 'organ-grid');
  for (const organ of house.organs) {
    const card = el('article', `organ-card ${organ.present ? 'present' : 'missing'}`);
    const top = el('div', 'organ-top');
    top.append(el('strong', '', organ.label), el('span', `state-pill ${organ.present ? 'good' : ''}`, organ.present ? 'present' : 'missing'));
    card.append(top, el('div', 'muted organ-role', organ.role));
    if (organ.present) {
      const repo = organ.repo;
      const [health, klass] = repoHealth(repo);
      const meta = el('div', 'organ-meta');
      meta.append(el('span', `mini-status ${klass}`, health), el('span', 'mini-status', stackLabel(repo)), el('span', 'mini-status', repo.branch || 'detached'));
      card.appendChild(meta);
      const open = el('button', 'quiet-button organ-open', 'Inspect');
      open.addEventListener('click', () => renderRepoDetail(repo));
      card.appendChild(open);
    } else {
      card.appendChild(el('div', 'muted tiny', 'Not found under configured roots. No conclusion about remote availability.'));
    }
    grid.appendChild(card);
  }
  organs.appendChild(grid);
  workspaceBody.appendChild(organs);

  $('#house-count').textContent = `${house.summary.core_organs_present}/${house.summary.core_organs_total}`;
}

async function copyCreatorHandoff(hit, output) {
  const ref = `${hit.root_id}:${hit.repo_path}/${hit.source_path}#L${hit.line}`;
  const head = hit.head ? `HEAD ${hit.head}` : 'no committed HEAD';
  const worktree = hit.dirty ? 'DIRTY worktree: content may not match HEAD' : 'working-tree excerpt; compare to HEAD before treating as commit evidence';
  const payload = [
    'CREATOR DESK / SOURCE HANDOFF (local, selected by human)',
    `Source: ${ref}`, `Git: ${head}`, worktree,
    `Excerpt: ${hit.snippet}`,
    'Task: Recall relevant context before creating. Separate source evidence, interpretation and unresolved gaps.',
    'This excerpt is a search hit, not the entire source or a verified project-native receipt.'
  ].join('\n');
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try { await navigator.clipboard.writeText(payload); output.textContent = 'Handoff copied; paste into the chosen Creator Workspace conversation.'; return; }
    catch (_) { /* manual fallback below */ }
  }
  const manual = el('textarea', 'handoff-manual');
  manual.readOnly = true; manual.value = payload;
  output.textContent = 'Clipboard unavailable. Select and copy this handoff manually:';
  output.appendChild(manual); manual.focus(); manual.select();
}

function renderCreatorHits(body, host) {
  clear(host);
  const note = el('div', 'muted tiny',
    `${body.hits.length} local hits / ${body.files_examined} bounded files inspected${body.truncated ? ' · LIMIT REACHED' : ''}. Search results do not establish project authority.`);
  host.appendChild(note);
  if (!body.hits.length) { host.appendChild(el('div', 'empty-state', 'No matching Markdown or plain-text lines in this checkout.')); return; }
  for (const hit of body.hits) {
    const card = el('article', 'card creator-hit');
    const marker = `${hit.root_id}:${hit.repo_path}/${hit.source_path}#L${hit.line}`;
    card.append(el('div', 'repo-name', marker), el('pre', 'raw-carrier', hit.snippet));
    card.appendChild(el('div', 'muted tiny', `${hit.head || 'unborn HEAD'} · ${hit.dirty ? 'DIRTY WORKTREE; excerpt not commit-anchored' : 'working tree; verify against commit before citing'}`));
    const button = el('button', 'quiet-button', 'Copy source handoff');
    button.type = 'button';
    const output = el('div', 'muted tiny creator-feedback');
    button.addEventListener('click', () => copyCreatorHandoff(hit, output));
    creatorV2Attach(card, hit, output);
    card.append(button, output);
    host.appendChild(card);
  }
}

function renderCreatorDesk() {
  state.view = 'creator'; syncNav('creator');
  setWorkspace('Creator Desk', 'Sources before synthesis');
  clear(workspaceBody);
  const desk = state.creator;
  if (!desk) { workspaceBody.appendChild(el('div', 'empty-state', 'Creator Desk registry unavailable.')); return; }
  const header = el('article', 'card');
  header.append(el('div', 'eyebrow', 'LOCAL SOURCES / HUMAN HANDOFF'),
    el('h2', '', 'Find a thread. Keep its origin.'),
    el('p', 'muted', 'Creator Workspace routing patterns are available as workflow guides. HOUSE does not invoke the plugin or send source material to external services.'));
  const laws = el('div', 'law-strip');
  desk.laws.forEach(item => laws.appendChild(el('span', 'law-chip', item)));
  header.appendChild(laws); workspaceBody.appendChild(header);

  const section = el('section', 'house-section');
  section.appendChild(el('div', 'section-heading', 'WORKFLOW DOORS / LOCAL PRESENCE ONLY'));
  const grid = el('div', 'action-grid');
  for (const workflow of desk.workflows) {
    const card = el('article', 'card creator-workflow');
    card.append(el('div', 'eyebrow', workflow.route), el('h2', '', workflow.label),
      el('p', 'muted', workflow.job),
      el('div', 'muted tiny', workflow.local_sources.length
        ? `${workflow.local_sources.length} checkout(s) discovered; inspection only`
        : 'No matching checkout discovered under configured roots.'));
    for (const repo of workflow.local_sources) {
      const button = el('button', 'quiet-button creator-source-button', `Inspect ${repo.name}`);
      button.type = 'button'; button.addEventListener('click', () => renderRepoDetail(repo));
      card.appendChild(button);
    }
    grid.appendChild(card);
  }
  section.appendChild(grid); workspaceBody.appendChild(section);

  const search = el('section', 'card creator-search');
  search.append(el('div', 'eyebrow', 'LOCAL SOURCE RECALL'),
    el('h2', '', 'Search one chosen checkout'),
    el('p', 'muted', 'Bounded README / Markdown / text inspection under configured roots. Select a source before drafting; no whole-repository upload.'));
  const form = el('form', 'creator-form');
  const chooser = el('select'); chooser.setAttribute('aria-label', 'Choose a local repository');
  for (const [i, repo] of state.repos.entries()) {
    const option = el('option', '', `${repo.root_id}:${repo.relative_path}`); option.value = String(i); chooser.appendChild(option);
  }
  const query = el('input'); query.type = 'search'; query.minLength = 2; query.maxLength = 100;
  query.required = true; query.placeholder = 'Search phrase'; query.setAttribute('aria-label', 'Search local source text');
  const submit = el('button', 'action-button', 'Find source lines'); submit.type = 'submit';
  if (!state.repos.length) submit.disabled = true;
  const results = el('div', 'creator-results');
  form.append(chooser, query, submit); search.append(form, results);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const repo = state.repos[Number(chooser.value)];
    if (!repo) return;
    results.textContent = 'Searching selected local checkout…';
    try {
      const params = new URLSearchParams({ root_id: repo.root_id, repo_path: repo.relative_path, query: query.value });
      const body = await api(`/api/creator/sources?${params}`);
      renderCreatorHits(body, results);
    } catch (error) {
      clear(results); results.appendChild(el('div', 'notice error', error.message || String(error)));
    }
  });
  workspaceBody.appendChild(search);
  creatorV2Render();
}

function renderMachine() {
  state.view = 'machine'; syncNav('machine');
  setWorkspace('Machine', 'Static node');
  clear(workspaceBody);
  const m = state.machine;
  if (!m) { workspaceBody.appendChild(el('div', 'empty-state', 'Machine sample unavailable.')); return; }
  const grid = el('div', 'metric-grid');
  grid.append(
    metricCard('CPU', `${m.cpu_percent.toFixed(1)}%`, m.cpu_percent),
    metricCard('Memory', `${m.memory.percent.toFixed(1)}%`, m.memory.percent),
    metricCard('Root disk', m.root_disk.available ? `${m.root_disk.percent.toFixed(1)}%` : 'unavailable', m.root_disk.percent),
    metricCard('Uptime', `${(m.uptime_seconds / 3600).toFixed(1)} h`)
  );
  const roots = el('article', 'card wide');
  roots.appendChild(el('h2', '', 'Configured storage'));
  for (const disk of m.configured_roots) {
    const line = el('div', 'definition-grid');
    line.append(el('dt', '', disk.root_id), el('dd', '', disk.available ? `${formatBytes(disk.used)} / ${formatBytes(disk.total)} · ${disk.percent.toFixed(1)}%` : 'path unavailable'));
    roots.appendChild(line);
  }
  const thermal = el('article', 'card wide');
  thermal.appendChild(el('h2', '', 'Thermals'));
  if (!m.temperatures.available) thermal.appendChild(el('div', 'muted', 'No supported thermal sensor readings were reported by this host.'));
  else for (const reading of m.temperatures.readings) {
    const line = el('div', 'definition-grid');
    line.append(el('dt', '', reading.label), el('dd', '', `${reading.current_c.toFixed(1)} °C`));
    thermal.appendChild(line);
  }
  grid.append(roots, thermal);
  workspaceBody.appendChild(grid);
  const hottest = m.temperatures.available ? Math.max(...m.temperatures.readings.map(r => r.current_c)) : null;
  $('#machine-temp').textContent = hottest === null ? '—' : `${hottest.toFixed(0)}°`;
}

function renderRepos() {
  state.view = 'repos'; syncNav('repos');
  setWorkspace('Repositories', 'What is here?');
  clear(workspaceBody);
  if (!state.repos.length) { workspaceBody.appendChild(el('div', 'empty-state', 'No Git repositories found under the configured roots.')); return; }
  const tools = el('div', 'repo-tools');
  const search = el('input'); search.type = 'search'; search.placeholder = 'Filter repositories…'; search.setAttribute('aria-label','Filter repositories');
  const summary = el('div', 'muted tiny', `${state.repos.length} repositories discovered under configured roots.`);
  tools.append(search, summary); workspaceBody.appendChild(tools);
  const list = el('div', 'repo-list');
  const draw = (query = '') => { clear(list); const needle = query.trim().toLowerCase();
  for (const repo of state.repos.filter(item => !needle || item.name.toLowerCase().includes(needle) || (item.relative_path || '').toLowerCase().includes(needle) || stackLabel(item).includes(needle))) {
    const row = el('button', 'repo-row');
    row.type = 'button';
    const left = el('div');
    left.append(el('div', 'repo-name', repo.name), el('div', 'repo-meta', `${repo.root_id}:${repo.relative_path} · ${repo.branch || 'detached'} @ ${repo.head || 'no HEAD'}`));
    const [health, healthClass] = repoHealth(repo);
    left.appendChild(el('div', 'repo-stack', stackLabel(repo)));
    const pill = el('span', `state-pill ${healthClass}`, health);
    row.append(left, pill);
    row.addEventListener('click', () => renderRepoDetail(repo));
    list.appendChild(row);
  }};
  draw(); search.addEventListener('input', () => draw(search.value));
  workspaceBody.appendChild(list);
}

function renderRepoDetail(repo) {
  state.view = 'repos'; syncNav('repos');
  setWorkspace('Repository', repo.name);
  clear(workspaceBody);
  const card = el('article', 'card');
  card.appendChild(el('h2', '', repo.dirty ? 'Working tree has changes' : 'Working tree clean'));
  const dl = el('dl', 'definition-grid');
  const fields = [
    ['Owner root', repo.root_id], ['Relative path', repo.relative_path], ['Branch', repo.branch || 'detached'],
    ['HEAD', repo.head || 'unborn'], ['Ahead', repo.ahead ?? 'no upstream'], ['Behind', repo.behind ?? 'no upstream'],
    ['Stack', stackLabel(repo)], ['Markers', repo.markers?.length ? repo.markers.join(', ') : 'none detected'], ['Host path', repo.path]
  ];
  for (const [key, value] of fields) dl.append(el('dt', '', key), el('dd', '', String(value)));
  card.appendChild(dl);
  const open = el('button', 'action-button', 'Inspect repository directory');
  open.addEventListener('click', () => inspectObject(repo.root_id, repo.relative_path));
  card.appendChild(open);
  workspaceBody.appendChild(card);
}

function renderObjects() {
  state.view = 'objects'; syncNav('objects');
  setWorkspace('Objects', 'Inspect a bounded path');
  clear(workspaceBody);
  const card = el('article', 'card');
  const form = el('form', 'object-form');
  const select = el('select'); select.id = 'object-root';
  for (const root of state.bootstrap.roots) { const option = el('option', '', root.id); option.value = root.id; select.appendChild(option); }
  const input = el('input'); input.id = 'object-path'; input.placeholder = 'relative/path/to/object'; input.autocomplete = 'off';
  const button = el('button', 'action-button', 'Inspect'); button.type = 'submit';
  form.append(select, input, button);
  form.addEventListener('submit', async (event) => { event.preventDefault(); await inspectObject(select.value, input.value); });
  card.append(form, el('div', 'muted', 'Paths are resolved inside the selected root. Absolute paths, parent traversal, and symlink escape are refused.'));
  workspaceBody.appendChild(card);
}

async function inspectObject(rootId, path) {
  try {
    const obj = await api(`/api/objects/inspect?root_id=${encodeURIComponent(rootId)}&path=${encodeURIComponent(path)}`);
    setWorkspace('Object', obj.path || rootId);
    clear(workspaceBody);
    const card = el('article', 'card');
    const dl = el('dl', 'definition-grid');
    [['Owner root', obj.root_id], ['Kind', obj.kind], ['Relative path', obj.path || '.'], ['Size', obj.size === null ? '—' : formatBytes(obj.size)]].forEach(([k,v]) => dl.append(el('dt','',k), el('dd','',String(v))));
    card.appendChild(dl);
    if (obj.preview !== null) {
      const pre = el('pre', 'code-preview', obj.preview);
      card.appendChild(pre);
      if (obj.preview_truncated) card.appendChild(el('div', 'muted tiny', 'Preview truncated at the configured byte ceiling.'));
    } else if (obj.entries) {
      const entries = el('div', 'object-entries');
      obj.entries.forEach(name => entries.appendChild(el('div', 'object-entry', name)));
      card.appendChild(entries);
    } else card.appendChild(el('div', 'muted', 'No text preview available for this object.'));
    workspaceBody.appendChild(card);
    await loadEvents();
  } catch (error) { showError(error); }
}

function renderApertureResult(record) {
  const host = $('#humanterminal-result');
  if (!host) return;
  clear(host);
  if (!record) {
    host.appendChild(el('div', 'empty-state', 'Open an aperture to preserve a sense-field cut. The deterministic v0.1 fixture knows only the ambiguous “bank” specimen.'));
    return;
  }

  const analysis = record.analysis;
  const summary = el('div', 'aperture-summary');
  summary.append(
    metricCard('Signal', String(analysis.signal.length)),
    metricCard('Context', String(analysis.context.length)),
    metricCard('Gap', String(analysis.gaps.length)),
    metricCard('Readings', String(analysis.readings.length))
  );
  host.appendChild(summary);

  const receipt = el('article', 'card aperture-receipt');
  receipt.appendChild(el('div', 'eyebrow', `Cut #${record.id} · ${analysis.status}`));
  receipt.appendChild(el('pre', 'raw-carrier', record.raw_text));
  receipt.appendChild(el('div', 'muted tiny', record.parent_id === null ? 'Root sense-field cut.' : `Descends from cut #${record.parent_id}. Earlier receipt remains unchanged.`));
  host.appendChild(receipt);

  const readings = el('article', 'card');
  readings.appendChild(el('h2', '', 'Sense field'));
  for (const reading of analysis.readings) {
    const item = el('div', 'sense-reading');
    item.append(el('div', 'reading-id', reading.id), el('div', '', reading.text), el('div', 'muted tiny', reading.basis));
    readings.appendChild(item);
  }
  if (analysis.gaps.length) {
    const gaps = el('div', 'gap-list');
    for (const gap of analysis.gaps) gaps.appendChild(el('div', 'gap-item', `${gap.code}: ${gap.text}`));
    readings.appendChild(gaps);
  }
  host.appendChild(readings);

  const triad = el('article', 'card');
  triad.appendChild(el('h2', '', 'TRIAD candidates'));
  if (!analysis.triad.length) triad.appendChild(el('div', 'muted', 'No semantic-role fixture emitted. The raw carrier remains unresolved.'));
  for (const candidate of analysis.triad) {
    const item = el('div', 'triad-item');
    item.append(el('span', 'triad-kind', candidate.kind), el('span', '', candidate.text));
    triad.appendChild(item);
  }
  host.appendChild(triad);
}

function updateParentLabel() {
  const label = $('#humanterminal-parent');
  if (!label) return;
  label.textContent = state.apertureParentId === null ? 'No parent cut selected.' : `Next cut descends from #${state.apertureParentId}.`;
}

function renderApertureHistory() {
  const host = $('#humanterminal-history');
  if (!host) return;
  clear(host);
  if (!state.apertureHistory.length) {
    host.appendChild(el('div', 'muted', 'No cuts yet.'));
    return;
  }
  for (const record of state.apertureHistory) {
    const row = el('button', 'history-row');
    row.type = 'button';
    const left = el('div');
    left.append(
      el('div', 'repo-name', `#${record.id} · ${record.analysis.status}`),
      el('div', 'repo-meta', `${timeLabel(record.created_at)} · ${record.analysis.readings.length} reading(s)${record.parent_id === null ? '' : ` · parent #${record.parent_id}`}`)
    );
    row.append(left, el('span', 'state-pill', 'inspect'));
    row.addEventListener('click', () => {
      state.apertureCurrent = record;
      state.apertureParentId = record.id;
      const raw = $('#humanterminal-input');
      if (raw) raw.value = record.raw_text;
      renderApertureResult(record);
      updateParentLabel();
    });
    host.appendChild(row);
  }
}

async function loadApertureHistory() {
  const body = await api('/api/aperture/history?limit=80');
  state.apertureHistory = body.sense_fields;
  if (state.view === 'humanterminal') renderApertureHistory();
}

async function submitAperture(event) {
  event.preventDefault();
  const raw = $('#humanterminal-input').value;
  const context = $('#humanterminal-context').value;
  const payload = { raw_text: raw };
  if (context.trim()) payload.context_text = context;
  if (state.apertureParentId !== null) payload.parent_id = state.apertureParentId;
  try {
    const record = await api('/api/aperture/analyze', { method: 'POST', body: JSON.stringify(payload) });
    state.apertureCurrent = record;
    state.apertureParentId = record.id;
    renderApertureResult(record);
    updateParentLabel();
    await Promise.all([loadApertureHistory(), loadEvents()]);
  } catch (error) {
    const host = $('#humanterminal-result');
    if (host) { clear(host); host.appendChild(el('div', 'notice error', error.message || String(error))); }
  }
}

function renderHumanTerminal() {
  state.view = 'humanterminal'; syncNav('humanterminal');
  setWorkspace('HumanTerminal', 'Hold the meanings open');
  clear(workspaceBody);
  const template = $('#humanterminal-template');
  workspaceBody.appendChild(template.content.cloneNode(true));
  $('.terminal-law').textContent = APERTURE_BOUNDARY;
  $('#humanterminal-form').addEventListener('submit', submitAperture);
  $('#humanterminal-new').addEventListener('click', () => {
    state.apertureParentId = null;
    state.apertureCurrent = null;
    $('#humanterminal-input').value = '';
    $('#humanterminal-context').value = '';
    updateParentLabel();
    renderApertureResult(null);
  });
  if (state.apertureCurrent) $('#humanterminal-input').value = state.apertureCurrent.raw_text;
  updateParentLabel();
  renderApertureResult(state.apertureCurrent);
  renderApertureHistory();
}

async function loadBroadcastDoor() { state.broadcast = await api('/api/broadcast/door'); if (state.view === 'house') renderHouse(); }
async function loadCreatorDesk() { state.creator = await api('/api/creator/desk'); if (state.view === 'creator') renderCreatorDesk(); }
async function loadMachine() { state.machine = await api('/api/machine'); if (state.view === 'machine') renderMachine(); }
async function loadRepos() { const body = await api('/api/repos'); state.repos = body.repos; $('#repo-count').textContent = String(state.repos.length); if (state.view === 'repos') renderRepos(); }
async function loadHouse() { state.house = await api('/api/house'); $('#house-count').textContent = `${state.house.summary.core_organs_present}/${state.house.summary.core_organs_total}`; if (state.view === 'house') renderHouse(); }
async function loadEvents() {
  const body = await api('/api/events?limit=80');
  const list = $('#event-list'); clear(list);
  if (!body.events.length) { list.appendChild(el('div', 'muted', 'No events recorded.')); return; }
  for (const event of body.events) {
    const item = el('article', 'event');
    item.append(el('div', 'event-kind', event.kind), el('div', 'event-time', timeLabel(event.created_at)), el('div', 'event-payload', JSON.stringify(event.payload)));
    list.appendChild(item);
  }
}

function renderRoots() {
  const list = $('#root-list'); clear(list);
  for (const root of state.bootstrap.roots) {
    const chip = el('div', 'root-chip'); chip.append(el('strong','',root.id), el('code','',root.path)); list.appendChild(chip);
  }
}

async function refreshCurrent() {
  try {
    if (state.view === 'house') await Promise.all([loadHouse(), loadRepos(), loadMachine(), loadBroadcastDoor()]);
    else if (state.view === 'machine') await loadMachine();
    else if (state.view === 'repos') await loadRepos();
    else if (state.view === 'objects') renderObjects();
    else if (state.view === 'creator') await Promise.all([loadRepos(), loadCreatorDesk()]);
    else if (state.view === 'maxhinal') await nativeMaxhinalLoad();
    else if (state.view === 'dogram-impact') { await loadRepos(); renderDogramImpactDesk(); }
    else { await loadApertureHistory(); renderHumanTerminal(); }
    await loadEvents();
  } catch (error) { showError(error); }
}

async function start() {
  try {
    state.bootstrap = await api('/api/bootstrap');
    $('#node-dot').classList.add('online'); $('#node-label').textContent = 'local supervisor online';
    renderRoots();
    await Promise.all([loadMachine(), loadRepos(), loadHouse(), loadCreatorDesk(), loadApertureHistory(), loadBroadcastDoor()]);
    await creatorV2Load();
    await nativeMaxhinalLoad();
    renderHouse();
    await loadEvents();
    window.setInterval(() => loadEvents().catch(() => {}), 5000);
  } catch (error) {
    $('#node-label').textContent = 'supervisor unavailable';
    showError(error);
  }
}

document.querySelectorAll('.nav-button').forEach(button => button.addEventListener('click', () => {
  const view = button.dataset.view;
  if (view === 'house') renderHouse(); else if (view === 'machine') renderMachine(); else if (view === 'repos') renderRepos(); else if (view === 'objects') renderObjects(); else if (view === 'creator') { renderCreatorDesk(); creatorV2Load().catch(showError); } else if (view === 'maxhinal') { renderNativeMaxhinal(); nativeMaxhinalLoad().catch(showError); } else if (view === 'dogram-impact') renderDogramImpactDesk(); else renderHumanTerminal();
}));
$('#refresh-view').addEventListener('click', refreshCurrent);
$('#refresh-events').addEventListener('click', () => loadEvents().catch(showError));

start();
