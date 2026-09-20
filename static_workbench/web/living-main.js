/* Living Main — a human-owned, read-only composition surface.
 * Source freshness is observed, never inferred from a branch name.
 * No execution, installation, remote fetch, persistence, or Git merge.
 */
const livingMainDesk = { selected: new Map(), preview: null, busy: false };
function livingMainKey(repo) { return repo.root_id + '\u0000' + repo.relative_path; }
function livingMainAvailable(repo) {
  return !!repo.root_id && !!repo.relative_path && /^[0-9a-f]{40}$/.test(repo.full_head || '') && !repo.dirty;
}
function livingMainInvalidate() { livingMainDesk.preview = null; }
function livingMainMark(label, value) {
  const chip = el('span', 'lm-mark ' + (value || ''), label);
  return chip;
}
function livingMainRenderReceipt(host) {
  clear(host);
  const preview = livingMainDesk.preview;
  if (!preview) {
    host.appendChild(el('p', 'muted', 'No composition preview yet. Choose exact local source versions, then inspect the proposed body.'));
    return;
  }
  const card = el('article', 'card lm-receipt');
  card.append(el('div', 'eyebrow', 'BODY-TIME / PREVIEW ONLY'), el('h2', '', 'A new configuration, not a new authority'));
  const id = el('code', 'lm-id', preview.configuration_id);
  card.appendChild(id);
  const marks = el('div', 'lm-marks');
  marks.append(livingMainMark('NOT EXECUTED', 'held'), livingMainMark('INTEGRATION NOT TESTED', 'held'), livingMainMark('AUTHORITY: NONE', 'held'));
  card.appendChild(marks);
  const roster = el('ol', 'lm-receipt-members');
  for (const member of preview.members) {
    const item = el('li');
    item.append(el('strong', '', member.root_id + ' / ' + member.relative_path),
      el('code', '', member.source_sha),
      el('span', 'muted tiny', 'Branch hint: ' + (member.branch_hint || 'detached') + ' · clean checkout; compatibility unverified'));
    roster.appendChild(item);
  }
  card.appendChild(roster);
  const copy = el('button', 'quiet-button', 'Copy composition manifest');
  copy.type = 'button';
  const feedback = el('div', 'muted tiny');
  copy.addEventListener('click', async () => {
    const text = JSON.stringify(preview, null, 2);
    if (navigator.clipboard?.writeText) {
      try { await navigator.clipboard.writeText(text); feedback.textContent = 'Manifest copied. This preview is not saved or executed.'; return; }
      catch (_) { /* manual copy below */ }
    }
    clear(feedback);
    feedback.appendChild(el('span', '', 'Clipboard unavailable. Copy this manifest manually:'));
    const manual = el('textarea', 'handoff-manual');
    manual.readOnly = true; manual.value = text;
    feedback.appendChild(manual); manual.focus(); manual.select();
  });
  card.append(copy, feedback, el('p', 'muted tiny',
    'The manifest identifies selected checkouts at observed commits. It does not lock dependencies, prove remote origin, test interoperability, or certify runtime readiness.'));
  host.appendChild(card);
}
function renderLivingMain() {
  state.view = 'living-main'; syncNav('living-main');
  setWorkspace('Living Main / Chronobody', 'Choose the body. Keep the history.');
  clear(workspaceBody);
  const hero = el('section', 'card lm-hero');
  const constellation = el('div', 'lm-constellation');
  for (let i = 0; i < 7; i += 1) constellation.appendChild(el('span', 'lm-star lm-star-' + i));
  hero.append(constellation, el('div', 'eyebrow', 'THE WORKSTATION / COMPOSITION DESK'),
    el('h2', '', 'A house with movable rooms.'),
    el('p', 'muted', 'Select clean local checkouts. Each chosen commit becomes one precisely named possibility in a composition preview. Nothing is merged, installed, or run.'),
    el('div', 'lm-mantra', 'BRANCH = POSSIBILITY  /  SHA = IDENTITY  /  PREVIEW ≠ PROMOTION'));
  workspaceBody.appendChild(hero);

  const layout = el('div', 'lm-layout');
  const shelf = el('section', 'card lm-shelf');
  shelf.append(el('div', 'eyebrow', '01 / SOURCE SHELF'), el('h2', '', 'Which rooms are coming?'));
  const filter = el('input'); filter.type = 'search'; filter.placeholder = 'Filter local checkouts…';
  filter.setAttribute('aria-label', 'Filter local checkouts');
  const count = el('div', 'muted tiny');
  const choices = el('div', 'lm-choices');
  shelf.append(filter, count, choices);
  const bench = el('section', 'card lm-bench');
  bench.append(el('div', 'eyebrow', '02 / HUMAN SELECTION'), el('h2', '', 'The composition table'));
  const chosen = el('div', 'lm-chosen');
  const feedback = el('div', 'lm-feedback');
  const previewButton = el('button', 'action-button', 'Preview this body');
  previewButton.type = 'button';
  const result = el('div', 'lm-result');
  const clearButton = el('button', 'quiet-button', 'Clear selection');
  clearButton.type = 'button';
  bench.append(chosen, previewButton, clearButton, feedback, result);
  layout.append(shelf, bench); workspaceBody.appendChild(layout);

  function renderChosen() {
    clear(chosen);
    const selected = Array.from(livingMainDesk.selected.values());
    chosen.appendChild(el('div', 'muted tiny', selected.length + '/24 exact-commit checkouts selected'));
    if (!selected.length) chosen.appendChild(el('p', 'muted', 'Select a clean checkout from the Source Shelf. Nothing enters this body automatically.'));
    for (const repo of selected) {
      const row = el('div', 'lm-chosen-row');
      const name = el('div');
      name.append(el('strong', '', repo.name), el('code', '', repo.full_head));
      const remove = el('button', 'quiet-button', 'Remove');
      remove.type = 'button'; remove.setAttribute('aria-label', 'Remove ' + repo.name);
      remove.addEventListener('click', () => {
        livingMainDesk.selected.delete(livingMainKey(repo)); livingMainInvalidate();
        renderChosen(); renderChoices(); livingMainRenderReceipt(result);
      });
      row.append(name, remove); chosen.appendChild(row);
    }
    previewButton.disabled = !selected.length || livingMainDesk.busy;
    clearButton.disabled = !selected.length || livingMainDesk.busy;
  }
  function renderChoices() {
    clear(choices);
    const search = filter.value.trim().toLowerCase();
    const candidates = state.repos.filter(repo =>
      (repo.name + ' ' + (repo.branch || '') + ' ' + (repo.relative_path || '')).toLowerCase().includes(search));
    count.textContent = candidates.length + ' visible checkouts · ' +
      state.repos.filter(livingMainAvailable).length + ' clean + commit-addressable';
    if (!candidates.length) choices.appendChild(el('p', 'muted', 'No local checkouts match. Fetching remote branches is a separate Source Dock operation.'));
    for (const repo of candidates) {
      const key = livingMainKey(repo);
      const row = el('label', 'lm-choice');
      const check = el('input'); check.type = 'checkbox';
      check.checked = livingMainDesk.selected.has(key);
      check.disabled = !livingMainAvailable(repo) || (!check.checked && livingMainDesk.selected.size >= 24) || livingMainDesk.busy;
      const details = el('span', 'lm-choice-details');
      details.append(el('strong', '', repo.name), el('span', 'muted tiny',
        (repo.branch || 'detached HEAD') + ' · ' + (repo.relative_path || '') + ' · ' +
        (repo.dirty ? 'dirty: held' : repo.full_head ? repo.full_head.slice(0, 12) : 'no committed HEAD')));
      row.append(check, details, livingMainMark(livingMainAvailable(repo) ? 'available' : 'held',
        livingMainAvailable(repo) ? 'available' : 'held'));
      check.addEventListener('change', () => {
        if (check.checked) livingMainDesk.selected.set(key, { ...repo });
        else livingMainDesk.selected.delete(key);
        livingMainInvalidate(); renderChosen(); renderChoices(); livingMainRenderReceipt(result);
      });
      choices.appendChild(row);
    }
  }
  filter.addEventListener('input', renderChoices);
  clearButton.addEventListener('click', () => {
    livingMainDesk.selected.clear(); livingMainInvalidate();
    feedback.textContent = ''; renderChosen(); renderChoices(); livingMainRenderReceipt(result);
  });
  previewButton.addEventListener('click', async () => {
    if (livingMainDesk.busy || !livingMainDesk.selected.size) return;
    livingMainDesk.busy = true; renderChosen(); renderChoices();
    feedback.textContent = 'Checking the selected local commits…';
    livingMainInvalidate(); livingMainRenderReceipt(result);
    try {
      const selections = Array.from(livingMainDesk.selected.values()).map(repo => ({
        root_id: repo.root_id, relative_path: repo.relative_path, expected_sha: repo.full_head,
      }));
      const preview = await api('/api/living-main/preview', {
        method: 'POST', headers: { 'X-Workbench-Session': state.bootstrap.session_token },
        body: JSON.stringify({ selections }),
      });
      livingMainDesk.preview = preview;
      feedback.textContent = 'Exact commits verified at preview. No code executed and no sources changed.';
    } catch (error) {
      feedback.textContent = 'Preview refused: ' + (error.message || String(error)) + '. Refresh the inventory and select again.';
    } finally {
      livingMainDesk.busy = false; renderChosen(); renderChoices(); livingMainRenderReceipt(result);
    }
  });
  renderChosen(); renderChoices(); livingMainRenderReceipt(result);
}
