'use strict';

const $ = id => document.getElementById(id);
let token = '';
let loops = [];
let folios = [];
let board = [];
let sourceRevision = '';
const el = (tag, cls = '', label = null) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (label !== null) node.textContent = label;
  return node;
};
function say(message, failed = false) {
  $('feedback').textContent = message;
  $('feedback').classList.toggle('error', failed);
}
async function api(path, data) {
  const init = {};
  if (data !== undefined) {
    init.method = 'POST';
    init.headers = {'Content-Type': 'application/json', 'x-workbench-session': token};
    init.body = JSON.stringify(data);
  }
  const response = await fetch(path, init);
  let result;
  try { result = await response.json(); }
  catch (_) { throw Error('Unexpected response from local Workbench'); }
  if (!response.ok) throw Error(result.detail || 'Local Workbench request failed');
  return result;
}
async function safe(callback) {
  try { await callback(); } catch (error) { say(error.message || 'Unexpected error', true); }
}
function ports(f) {
  return {
    input: {class: f.layers[0].input_class, port: f.layers[0].input_port},
    output: {class: f.layers.at(-1).output_class, port: f.layers.at(-1).output_port},
  };
}
function checkBoard(items) {
  const gaps = [];
  items.forEach((f, i) => {
    for (const obstruction of f.internal_passage.obstructions) {
      gaps.push({kind: 'within', index: i, reason: obstruction.reason,
        available: obstruction.available, required: obstruction.required});
    }
  });
  for (let i = 0; i < items.length - 1; i++) {
    const left = ports(items[i]).output, right = ports(items[i + 1]).input;
    if (left.class !== right.class || left.port !== right.port) {
      gaps.push({kind: 'between', index: i,
        reason: left.class !== right.class ? 'abstract_class_gap' : 'concrete_lift_gap',
        available: left, required: right});
    }
  }
  return gaps;
}
function renderBoard() {
  const host = $('board');
  host.replaceChildren();
  if (!board.length) host.append(el('div', 'empty-state', 'Select a folio and add it to the board.'));
  const gaps = checkBoard(board);
  board.forEach((folio, index) => {
    const tile = el('article', 'book-tile');
    const p = ports(folio);
    tile.append(
      el('small', '', 'DOMINO ' + (index + 1) + ' · ' + folio.id.slice(0, 8)),
      el('strong', '', folio.title),
      el('small', '', 'IN ' + p.input.class + ':' + p.input.port),
      el('small', '', 'OUT ' + p.output.class + ':' + p.output.port),
      el('small', '', folio.snapshot_sha256.slice(0, 12)),
    );
    host.append(tile);
    if (index < board.length - 1) {
      const gap = gaps.find(g => g.kind === 'between' && g.index === index);
      host.append(el('div', gap ? 'book-gap' : 'notice',
        gap ? 'MISSING JOIN\n' + gap.available.class + ':' + gap.available.port
          + ' ≠ ' + gap.required.class + ':' + gap.required.port
        : '→\nExact declared ports meet'));
    }
  });
  $('save-board').disabled = board.length < 2 || board.length > 8;
  $('remove').disabled = board.length === 0;
  const notice = $('passage');
  if (board.length < 2) {
    notice.textContent = 'Lay at least two folios to inspect the joins.';
  } else if (gaps.length) {
    notice.textContent = 'ABSTRACT SKETCH · ' + gaps.length
      + ' unresolved join(s), including internal folio gaps if present. '
      + 'Preserve the arrangement to keep the exact missing connection visible.';
  } else {
    notice.textContent = 'SYNTHETIC PORTS MATCH · This is a drawing-level arrangement, '
      + 'not a witnessed project execution or authorization to run.';
  }
}
function renderFolios() {
  const host = $('folios');
  host.replaceChildren();
  if (!folios.length) {
    host.append(el('div', 'muted', 'No folios yet. Record a MADDLOOP and inscribe it here.'));
    return;
  }
  for (const f of folios) {
    const card = el('article', 'book-plate');
    const ports = f.ports;
    card.append(
      el('small', '', 'MACHINE FOLIO · ' + f.id.slice(0, 8)),
      el('h3', '', f.title),
      el('p', '', f.purpose),
      el('div', 'book-ports',
        '◁ ' + ports.input.class + ':' + ports.input.port
        + '   |   ' + ports.output.class + ':' + ports.output.port + ' ▷'),
      el('small', '', 'Frozen loop ' + f.loop_id.slice(0, 10)
        + ' · revision ' + f.revision_id.slice(0, 10)
        + ' · sha256 ' + f.snapshot_sha256.slice(0, 16)),
    );
    if (f.internal_passage.obstructions.length) {
      card.append(el('div', '', 'Internal gaps: ' + f.internal_passage.obstructions.length
        + '. This page remains a candidate.'));
    }
    const add = el('button', 'action-button', '+ Lay this domino');
    add.type = 'button';
    add.disabled = board.length >= 8;
    add.addEventListener('click', () => {
      if (board.length >= 8) return;
      board.push(f);
      renderBoard();
      renderFolios();
      say('Folio laid as domino ' + board.length + '. No action was executed.');
    });
    card.append(add);
    host.append(card);
  }
}
async function loadFolios() {
  folios = (await api('/api/machines/folios')).folios;
  renderFolios();
  renderBoard();
}
async function loadSource() {
  const select = $('loop-select');
  sourceRevision = '';
  $('inscribe').disabled = true;
  const id = select.value;
  if (!id) { $('source-note').textContent = 'Choose a source loop first.'; return; }
  const source = await api('/api/maddloop/loops/' + encodeURIComponent(id));
  sourceRevision = source.head_revision_id;
  $('source-note').textContent = 'Freeze exact revision ' + sourceRevision
    + ' / ' + source.layers.length + ' layer(s) / digest ' + source.snapshot_sha256
    + '. Later edits to the loop will not change this folio.';
  $('inscribe').disabled = false;
}
async function loadBoards() {
  const rows = (await api('/api/machines/boards')).boards;
  const host = $('boards');
  host.replaceChildren();
  if (!rows.length) { host.append(el('div', 'muted', 'No preserved arrangements.')); return; }
  for (const row of rows) {
    const item = el('div', 'book-line');
    item.append(el('span', '', row.title + ' · ' + row.status));
    const see = el('button', 'quiet-button', 'Open receipt');
    see.type = 'button';
    see.addEventListener('click', () => safe(async () => {
      const saved = await api('/api/machines/boards/' + row.id);
      board = saved.folios;
      renderBoard();
      renderFolios();
      say('Opened a frozen arrangement · ' + row.id
        + '. Editing this desk will not rewrite its preserved receipt.');
    }));
    item.append(see);
    host.append(item);
  }
}
$('loop-select').addEventListener('change', () => safe(loadSource));
$('folio-form').addEventListener('submit', event => {
  event.preventDefault();
  safe(async () => {
    const input = new FormData(event.target);
    if (!sourceRevision) throw Error('Choose and inspect a source loop first.');
    const result = await api('/api/machines/folios', {
      title: input.get('title'), purpose: input.get('purpose'),
      loop_id: input.get('loop_id'), expected_revision_id: sourceRevision,
    });
    event.target.reset();
    sourceRevision = '';
    $('inscribe').disabled = true;
    $('source-note').textContent = 'Select a loop to inspect its current revision.';
    await loadFolios();
    say('Inscribe complete · folio ' + result.id + ' / frozen revision ' + result.revision_id);
  });
});
$('clear').addEventListener('click', () => {board=[];renderBoard();renderFolios();say('Draft board cleared; preserved folios and arrangements remain.');});
$('remove').addEventListener('click', () => {board.pop();renderBoard();renderFolios();say('Last domino removed from the unsaved board.');});
$('board-form').addEventListener('submit', event => {
  event.preventDefault();
  safe(async () => {
    if (board.length < 2 || board.length > 8) throw Error('Choose 2-8 folios in sequence.');
    const title = new FormData(event.target).get('title');
    const result = await api('/api/machines/boards', {title, folio_ids: board.map(f => f.id)});
    await loadBoards();
    say('Frozen arrangement ' + result.id + ' saved with status ' + result.result.status
      + '. No physical or project execution occurred.');
    event.target.reset();
  });
});
safe(async () => {
  const bootstrap = await api('/api/bootstrap');
  token = bootstrap.session_token;
  loops = (await api('/api/maddloop/loops')).loops;
  const select = $('loop-select');
  select.replaceChildren();
  const blank = el('option', '', 'Choose a recorded loop'); blank.value = '';
  select.append(blank);
  for (const loop of loops) {
    const option = el('option', '', loop.title); option.value = loop.id; select.append(option);
  }
  await loadFolios();
  await loadBoards();
  say('Book ready. Inscribe a source-linked machine folio, then lay two or more dominoes.');
});
