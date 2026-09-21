'use strict';

let token = null;
let current = null;
let loopTimer = null;
let loopPasses = 0;
let loopBusy = false;
let cycleLoopId = null;
let cycleRevisionId = null;

const $ = id => document.getElementById(id);
const show = (message, error = false) => {
  $('feedback').textContent = message;
  $('feedback').classList.toggle('error', error);
};
const element = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
async function api(path, data) {
  const options = {};
  if (data !== undefined) {
    options.method = 'POST';
    options.headers = {'Content-Type': 'application/json', 'x-workbench-session': token};
    options.body = JSON.stringify(data);
  }
  const response = await fetch(path, options);
  let body;
  try { body = await response.json(); } catch (_) { throw Error('Unexpected supervisor response'); }
  if (!response.ok) throw Error(body.detail || 'Request failed (' + response.status + ')');
  return body;
}
function layerFrom(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  delete data.title;
  return data;
}
async function loadList(selectId) {
  const result = await api('/api/maddloop/loops');
  const picker = $('loop-select');
  picker.replaceChildren(element('option', '', 'No loop selected'));
  picker.firstChild.value = '';
  for (const item of result.loops) {
    const option = element('option', '', item.title);
    option.value = item.id;
    picker.appendChild(option);
  }
  picker.value = selectId || '';
}
function render() {
  const active = Boolean(current);
  for (const id of ['play', 'branch', 'overdub']) $(id).disabled = !active || Boolean(loopTimer);
  $('loop-start').disabled = !active || Boolean(loopTimer);
  $('loop-stop').disabled = !loopTimer;
  $('loop-seconds').disabled = Boolean(loopTimer);
  $('loop-title').textContent = active ? current.title : 'Choose or record a loop';
  $('loop-meta').textContent = active
    ? 'Loop ' + current.id + ' · revision ' + current.head_revision_id
       + ' · digest ' + current.snapshot_sha256
       + (current.parent_loop_id ? ' · branch of ' + current.parent_loop_id : '')
    : 'No source selected.';
  const passage = $('passage'), layers = $('layers'), encounters = $('encounters');
  layers.replaceChildren();
  encounters.replaceChildren();
  if (!active) {
    passage.textContent = 'The exact join check appears here.';
    encounters.textContent = 'No encounters yet.';
    return;
  }
  const gaps = current.passage.obstructions;
  passage.textContent = gaps.length
    ? 'CANDIDATE ONLY · ' + gaps.length + ' join obstruction(s). Playback will preserve the gap as a preview, not claim a traversable route.'
    : 'SYNTHETIC ROUTE WITNESSED · Adjacent concrete port identifiers match. This is not an execution permit.';
  current.layers.forEach((item, index) => {
    const card = element('article', 'loop-layer');
    card.append(
      element('div', 'eyebrow', 'LAYER ' + (index + 1) + ' · ' + item.kind),
      element('h2', '', item.label),
      element('pre', '', item.body),
      element('div', 'muted tiny', 'Input ' + item.input_class + ':' + item.input_port
        + ' → output ' + item.output_class + ':' + item.output_port),
      element('div', 'muted tiny', 'Immutable source ' + item.source_id + ' · ' + item.source_created_at),
    );
    layers.appendChild(card);
    const gap = gaps.find(g => g.between_layers[0] === index);
    if (gap) {
      const obstruction = element('article', 'loop-layer loop-gap');
      obstruction.append(
        element('strong', '', 'MISSING JOIN · ' + gap.reason),
        element('div', 'muted', 'Available ' + gap.available.class + ':' + gap.available.port
          + ' / required ' + gap.required.class + ':' + gap.required.port),
      );
      layers.appendChild(obstruction);
    }
  });
  if (!current.encounters.length) {
    encounters.textContent = 'No encounters yet.';
    return;
  }
  for (const encounter of current.encounters) {
    const row = element('article', 'loop-layer');
    row.append(
      element('div', 'eyebrow', encounter.status + ' · ' + encounter.kind),
      element('div', 'muted tiny', encounter.id + ' · ' + encounter.created_at),
      element('div', 'muted tiny', 'Snapshot ' + encounter.snapshot_sha256),
      element('div', 'muted tiny', 'Sources: ' + encounter.receipt.source_ids.join(', ')),
    );
    encounters.appendChild(row);
  }
}
async function select(id) {
  stopLoop();
  current = id ? await api('/api/maddloop/loops/' + encodeURIComponent(id)) : null;
  $('loop-select').value = id || '';
  render();
}
async function safe(fn) {
  try { await fn(); } catch (error) {
    show(error.message || 'Unexpected error', true);
    if (/changed since review/.test(error.message || '') && current) await select(current.id);
  }
}
function stopLoop() {
  if (loopTimer !== null) clearInterval(loopTimer);
  loopTimer = null;
  cycleLoopId = null;
  cycleRevisionId = null;
  render();
}
async function tickLoop() {
  if (!loopTimer || loopBusy) return;
  if (!current || current.id !== cycleLoopId || current.head_revision_id !== cycleRevisionId) {
    stopLoop();
    show('Loop stopped: arrangement changed. Review the new revision before re-arming.', true);
    return;
  }
  loopBusy = true;
  try {
    const id = cycleLoopId;
    const result = await api('/api/maddloop/loops/' + id + '/encounters', {
      expected_revision_id: cycleRevisionId,
    });
    loopPasses += 1;
    // A STOP cannot undo a request already in flight, but it prevents future passes.
    if (current && current.id === id) {
      current = await api('/api/maddloop/loops/' + id);
      render();
    }
    if (!loopTimer) return;
    show('LOOP · preview pass ' + loopPasses + '/8 · ' + result.status
      + ' · encounter ' + result.id + '. No project action was executed.');
    if (loopPasses >= 8) {
      stopLoop();
      show('LOOP · 8 distinct read-only preview encounters recorded. Re-arm for another set.');
    }
  } catch (error) {
    stopLoop();
    show('Loop stopped: ' + (error.message || 'preview failed'), true);
  } finally {
    loopBusy = false;
  }
}
$('loop-start').addEventListener('click', () => safe(async () => {
  if (!current || loopTimer) return;
  const seconds = Number($('loop-seconds').value);
  if (!Number.isInteger(seconds) || seconds < 2 || seconds > 60) {
    throw Error('Choose a cycle interval from 2 to 60 seconds.');
  }
  loopPasses = 0;
  cycleLoopId = current.id;
  cycleRevisionId = current.head_revision_id;
  loopTimer = setInterval(tickLoop, seconds * 1000);
  render();
  show('LOOP armed. Each pass is a separate local preview; STOP ends future passes.');
  await tickLoop();
}));
$('loop-stop').addEventListener('click', () => {
  stopLoop();
  show('STOP · No further preview passes scheduled. An in-flight pass may finish.');
});
window.addEventListener('pagehide', stopLoop);
document.addEventListener('visibilitychange', () => {
  if (document.hidden && loopTimer) {
    stopLoop();
    show('LOOP stopped when the page became hidden.');
  }
});
$('loop-select').addEventListener('change', e => safe(async () => {
  await select(e.target.value);
  show(current ? 'Selected ' + current.title : 'No loop selected');
}));
$('create-form').addEventListener('submit', e => {
  e.preventDefault();
  safe(async () => {
    const data = new FormData(e.target);
    const result = await api('/api/maddloop/loops', {
      title: data.get('title'), layer: {kind: 'text', label: data.get('label'), body: data.get('body')},
    });
    await loadList(result.id);
    await select(result.id);
    e.target.reset();
    show('REC · New immutable source and first revision saved.');
  });
});
$('overdub-form').addEventListener('submit', e => {
  e.preventDefault();
  safe(async () => {
    if (!current) return;
    const result = await api('/api/maddloop/loops/' + current.id + '/overdub', {
      expected_revision_id: current.head_revision_id, layer: layerFrom(e.target),
    });
    current = result;
    render();
    e.target.reset();
    show('OVERDUB · New revision saved. Earlier sources and revisions are unchanged.');
  });
});
$('branch').addEventListener('click', () => safe(async () => {
  if (!current) return;
  const name = window.prompt('Name the new branch', current.title + ' / branch');
  if (name === null) return;
  const result = await api('/api/maddloop/loops/' + current.id + '/branch', {
    expected_revision_id: current.head_revision_id, title: name,
  });
  await loadList(result.id);
  await select(result.id);
  show('BRANCH · New loop saved with a pointer to its parent revision.');
}));
$('play').addEventListener('click', () => safe(async () => {
  if (!current) return;
  const encounter = await api('/api/maddloop/loops/' + current.id + '/encounters', {
    expected_revision_id: current.head_revision_id,
  });
  await select(current.id);
  show('PLAY · ' + encounter.status + ' · encounter ' + encounter.id
    + '. This is a new read-only encounter, not action execution.');
}));
$('refresh').addEventListener('click', () => safe(async () => {
  await loadList(current && current.id);
  if (current) await select(current.id);
  show('Local Workbench loop state refreshed.');
}));
safe(async () => {
  const bootstrap = await api('/api/bootstrap');
  token = bootstrap.session_token;
  await loadList();
  render();
  show('Pedal ready. Record the first layer to begin.');
});
