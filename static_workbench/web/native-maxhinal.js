/* HOUSE's native Maxhinal: only explicit local fuel, no Daily Slice gas impersonation. */
const nativeMaxhinalState = {
  selected: [], preview: null, info: null, packs: [], rides: [], current: null,
};

async function nativeMaxhinalLoad() {
  const [info, packs, rides] = await Promise.all([
    api('/api/house-maxhinal'), api('/api/creator/packs'), api('/api/house-maxhinal/rides'),
  ]);
  nativeMaxhinalState.info = info;
  nativeMaxhinalState.packs = packs.packs;
  nativeMaxhinalState.rides = rides.rides;
  if (state.view === 'maxhinal') renderNativeMaxhinal();
}

function nativeMaxhinalMessage(host, message, error = false) {
  host.appendChild(el('div', error ? 'notice error' : 'notice', message));
}

function nativeMaxhinalAppendFile(host) {
  const form = el('form', 'native-fuel-form');
  form.appendChild(el('h2', '', 'Add one explicitly chosen local file'));
  const roots = el('select'); roots.setAttribute('aria-label', 'Configured local fuel root');
  for (const root of state.bootstrap.roots) {
    const option = el('option', '', root.id + ' · ' + root.path);
    option.value = root.id; roots.appendChild(option);
  }
  const relative = el('input'); relative.required = true; relative.maxLength = 512;
  relative.placeholder = 'relative/path/to/file.txt'; relative.setAttribute('aria-label', 'Root-relative fuel file path');
  const add = el('button', 'quiet-button', 'Select file as fuel'); add.type = 'submit';
  const output = el('div', 'creator-feedback');
  form.append(roots, relative, add, output);
  form.addEventListener('submit', event => {
    event.preventDefault();
    clear(output);
    const selected = nativeMaxhinalState.selected;
    if (selected.length >= 4) {
      nativeMaxhinalMessage(output, 'Select no more than four fuel items.', true); return;
    }
    const item = { kind: 'file', root_id: roots.value, path: relative.value.trim() };
    if (selected.some(s => s.kind === 'file' && s.root_id === item.root_id && s.path === item.path)) {
      nativeMaxhinalMessage(output, 'File already selected.', true); return;
    }
    selected.push(item); nativeMaxhinalState.preview = null;
    nativeMaxhinalRenderSelection();
    relative.value = '';
  });
  host.appendChild(form);
}

function nativeMaxhinalAppendPack(host) {
  const section = el('div', 'native-fuel-form');
  section.appendChild(el('h2', '', 'Or add a saved Creator Desk source pack'));
  const choose = el('select'); choose.setAttribute('aria-label', 'Select saved source pack as fuel');
  for (const pack of nativeMaxhinalState.packs) {
    const option = el('option', '', 'Pack #' + pack.id + ' · ' + pack.source_count + ' passages');
    option.value = String(pack.id); choose.appendChild(option);
  }
  const add = el('button', 'quiet-button', 'Select saved pack as fuel');
  add.type = 'button'; add.disabled = nativeMaxhinalState.packs.length === 0;
  const note = el('div', 'creator-feedback');
  add.addEventListener('click', () => {
    clear(note);
    const selected = nativeMaxhinalState.selected;
    const pack_id = Number(choose.value);
    if (!pack_id || selected.length >= 4 || selected.some(x => x.kind === 'source_pack' && x.pack_id === pack_id)) {
      nativeMaxhinalMessage(note, 'Choose a distinct saved pack; limit four fuel items.', true); return;
    }
    selected.push({ kind: 'source_pack', pack_id });
    nativeMaxhinalState.preview = null;
    nativeMaxhinalRenderSelection();
  });
  section.append(choose, add, note);
  host.appendChild(section);
}

function nativeMaxhinalRenderSelection() {
  const host = $('#native-maxhinal-selection');
  if (!host) return;
  clear(host);
  const s = nativeMaxhinalState;
  host.appendChild(el('div', 'eyebrow', 'FUEL RACK · ' + s.selected.length + '/4 EXPLICIT ITEMS'));
  s.selected.forEach((item, index) => {
    const row = el('div', 'creator-selected-row');
    row.appendChild(el('span', '', item.kind === 'file'
      ? item.root_id + ':' + item.path
      : 'Saved Creator Desk pack #' + item.pack_id));
    const remove = el('button', 'quiet-button', 'Remove');
    remove.type = 'button';
    remove.addEventListener('click', () => {
      s.selected.splice(index, 1); s.preview = null; nativeMaxhinalRenderSelection();
    });
    row.appendChild(remove); host.appendChild(row);
  });
  const preview = el('button', 'action-button', 'Review this fuel before spinning');
  preview.disabled = s.selected.length === 0; preview.type = 'button';
  host.appendChild(preview);
  const result = el('div', 'native-fuel-preview');
  host.appendChild(result);
  preview.addEventListener('click', async () => {
    clear(result);
    s.preview = null;
    try {
      const payload = { fuels: s.selected };
      const packet = await creatorV2Write('/api/house-maxhinal/fuel/preview', payload);
      s.preview = packet;
      result.append(el('div', 'repo-name', 'Fuel digest SHA-256: ' + packet.fuel_sha256),
        el('p', 'muted tiny', 'Review every excerpt and filename. Metadata-only files have NOT been interpreted as image, sound or binary content.'));
      packet.fuels.forEach((fuel, i) => {
        const card = el('article', 'creator-preview-source');
        card.append(el('div', 'repo-name', 'FUEL ' + (i + 1) + ' · ' + (fuel.kind === 'file'
          ? fuel.root_id + ':' + fuel.path : 'saved source pack #' + fuel.pack_id)),
          el('div', 'muted tiny', (fuel.sha256 || fuel.pack_sha256) + ' · ' + fuel.reading));
        if (fuel.kind === 'file') card.appendChild(el('div', 'muted tiny', fuel.byte_size + ' bytes · ' + fuel.media_type));
        if (fuel.excerpt !== null && fuel.excerpt !== undefined) {
          card.appendChild(el('pre', 'raw-carrier', fuel.excerpt));
        }
        result.appendChild(card);
      });
      const spinForm = el('form', 'native-spin-form');
      const mode = el('select'); mode.setAttribute('aria-label', 'HOUSE Maxhinal chamber');
      s.info.modes.forEach(name => {
        const option = el('option', '', name); option.value = name; mode.appendChild(option);
      });
      const seed = el('input'); seed.maxLength = 100; seed.value = '0'; seed.placeholder = 'Reproducible seed';
      seed.setAttribute('aria-label', 'HOUSE Maxhinal spin seed');
      const question = el('textarea'); question.rows = 3; question.maxLength = 400;
      question.placeholder = 'What do you want to explore? (optional)';
      question.setAttribute('aria-label', 'Human creative question');
      const spinButton = el('button', 'action-button', 'Spin reviewed fuel and save local ride');
      spinButton.type = 'submit';
      const status = el('div', 'creator-feedback');
      spinForm.append(mode, seed, question, spinButton, status);
      spinForm.addEventListener('submit', async event => {
        event.preventDefault(); spinButton.disabled = true; clear(status);
        try {
          const response = await creatorV2Write('/api/house-maxhinal/spin', {
            fuels: s.selected, expected_fuel_sha256: packet.fuel_sha256,
            mode: mode.value, seed: seed.value, question: question.value,
          });
          s.current = { id: response.receipt.id, ride_sha256: response.receipt.ride_sha256, ...response.ride };
          nativeMaxhinalMessage(status, 'Saved local native ride #' + response.receipt.id + '. Sources were not modified.');
          const latest = await api('/api/house-maxhinal/rides');
          s.rides = latest.rides;
          nativeMaxhinalRenderHistory();
          nativeMaxhinalRenderRide();
        } catch (error) {
          nativeMaxhinalMessage(status, (error.message || String(error)) + ' · No ride was saved; review fuel again if it changed.', true);
          spinButton.disabled = false;
        }
      });
      result.appendChild(spinForm);
    } catch (error) {
      nativeMaxhinalMessage(result, error.message || String(error), true);
    }
  });
}

function nativeMaxhinalRenderRide() {
  const host = $('#native-maxhinal-ride');
  if (!host) return;
  clear(host);
  const ride = nativeMaxhinalState.current;
  if (!ride) {
    host.appendChild(el('p', 'muted', 'No native spin selected. Choose fuel, preview, and spin—or open a saved ride.'));
    return;
  }
  host.append(el('div', 'eyebrow', 'HOUSE NATIVE RIDE #' + ride.id + ' · ' + ride.mode),
    el('div', 'muted tiny', 'Ride SHA-256: ' + ride.ride_sha256 + ' · Fuel SHA-256: ' + ride.fuel_sha256),
    el('p', 'muted tiny', ride.notice));
  ride.outputs.forEach((item, i) => {
    const card = el('article', 'creator-preview-source');
    card.appendChild(el('div', 'repo-name', 'PROJECTION ' + (i + 1) + ' · ' + item.kind));
    card.appendChild(el('pre', 'raw-carrier', JSON.stringify(item, null, 2)));
    host.appendChild(card);
  });
  ride.residuals.forEach(item => host.appendChild(el('div', 'gap-item', 'RESIDUAL: ' + item)));
  ride.bad_spins.forEach(item => host.appendChild(el('div', 'gap-item', 'BAD SPIN: ' + item)));
  const copy = el('button', 'quiet-button', 'Copy this native ride for a Creator Desk draft');
  copy.type = 'button';
  const status = el('div', 'creator-feedback');
  copy.addEventListener('click', async () => {
    const text = [
      'HOUSE NATIVE MAXHINAL / HUMAN-SELECTED LOCAL RIDE',
      'Local ride #' + ride.id + ' · ' + ride.ride_sha256,
      'Mode ' + ride.mode + ' · Seed ' + ride.seed,
      'Exact source references:\n' + JSON.stringify(ride.source_refs, null, 2),
      'Derived projections:\n' + JSON.stringify(ride.outputs, null, 2),
      'Residuals:\n' + ride.residuals.join('\n'),
      'Rejected spins:\n' + ride.bad_spins.join('\n'),
      'HOUSE-native creative transformation. Not evidence, project canon, or Daily Slice Maxhinal output.',
    ].join('\n\n');
    clear(status);
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        nativeMaxhinalMessage(status, 'Copied by explicit request. Paste into a Creator Desk draft when you choose.');
        return;
      } catch (_) { /* fallback */ }
    }
    const area = el('textarea', 'handoff-manual'); area.readOnly = true; area.value = text;
    status.appendChild(area); area.focus(); area.select();
  });
  host.append(copy, status);
  graftRoundRenderForRide(ride, host);
  graftRenderForRide(ride, host);
}

function nativeMaxhinalRenderHistory() {
  const host = $('#native-maxhinal-history');
  if (!host) return;
  clear(host);
  host.appendChild(el('h2', '', 'Saved native spins'));
  for (const item of nativeMaxhinalState.rides) {
    const open = el('button', 'quiet-button creator-source-button',
      'Inspect #' + item.id + ' · ' + item.mode + ' · ' + item.ride_sha256.slice(0, 12));
    open.type = 'button';
    open.addEventListener('click', async () => {
      try {
        nativeMaxhinalState.current = await api('/api/house-maxhinal/rides/' + item.id);
        nativeMaxhinalRenderRide();
      } catch (error) {
        nativeMaxhinalMessage(host, error.message || String(error), true);
      }
    });
    host.appendChild(open);
  }
}

function renderNativeMaxhinal() {
  state.view = 'maxhinal'; syncNav('maxhinal');
  setWorkspace('HOUSE Maxhinal', 'Any selected local fuel, no counterfeit meaning');
  clear(workspaceBody);
  const header = el('article', 'card');
  header.append(el('div', 'eyebrow', 'NATIVE / EXPERIMENTAL / DETERMINISTIC'),
    el('h2', '', 'The HOUSE Maxhinal'),
    el('p', 'muted', 'This is a separate HOUSE instrument inspired by the Daily Slice Maxhinal. Pick specific files under configured roots or saved Creator Desk source packs. It does not scan your computer, run selected code, interpret binary media, or change project files.'));
  workspaceBody.appendChild(header);
  const rack = el('section', 'card native-maxhinal-rack');
  nativeMaxhinalAppendFile(rack);
  nativeMaxhinalAppendPack(rack);
  const selection = el('div'); selection.id = 'native-maxhinal-selection';
  rack.appendChild(selection); workspaceBody.appendChild(rack);
  const result = el('section', 'card');
  result.appendChild(el('h2', '', 'Ride receipt / projections / fog'));
  const ride = el('div'); ride.id = 'native-maxhinal-ride';
  result.appendChild(ride); workspaceBody.appendChild(result);
  const history = el('section', 'card'); history.id = 'native-maxhinal-history';
  workspaceBody.appendChild(history);
  nativeMaxhinalRenderSelection();
  nativeMaxhinalRenderRide();
  nativeMaxhinalRenderHistory();
}
