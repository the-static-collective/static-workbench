/* Creator Desk v0.2: explicit local source selection and immutable draft shelf.
 * Loaded before app.js; handlers only run after the HOUSE app has initialized.
 */
function creatorV2State() {
  if (!state.creatorV2) state.creatorV2 = {
    selected: [], preview: null, packs: [], drafts: [], pack: null, draft: null,
  };
  return state.creatorV2;
}
function creatorV2Key(item) {
  return [item.root_id, item.repo_path, item.source_path, item.line].join('\u0000');
}
async function creatorV2Write(path, payload) {
  return api(path, {
    method: 'POST',
    headers: { 'X-Workbench-Session': state.bootstrap.session_token },
    body: JSON.stringify(payload),
  });
}
function creatorV2Message(host, message, isError) {
  host.appendChild(el('div', isError ? 'notice error' : 'notice', message));
}
function creatorV2Attach(card, hit, output) {
  const button = el('button', 'quiet-button', 'Select for source pack');
  button.type = 'button';
  button.addEventListener('click', () => {
    const desk = creatorV2State();
    const selection = {
      root_id: hit.root_id, repo_path: hit.repo_path, source_path: hit.source_path,
      line: hit.line, file_sha256: hit.file_sha256, snippet: hit.snippet,
    };
    if (desk.selected.some(item => creatorV2Key(item) === creatorV2Key(selection))) {
      output.textContent = 'This source line is already selected.';
      return;
    }
    if (desk.selected.length >= 8) {
      output.textContent = 'Source packs are limited to eight lines.';
      return;
    }
    desk.selected.push(selection);
    desk.preview = null;
    creatorV2RenderSelection();
    output.textContent = 'Selected. Review the complete source pack before saving.';
  });
  card.appendChild(button);
}
function creatorV2Render() {
  const s = creatorV2State();
  const selection = el('section', 'card creator-selection');
  selection.appendChild(el('h2', '', 'Source pack / deliberate selection'));
  const body = el('div');
  body.id = 'creator-selected';
  selection.appendChild(body);
  workspaceBody.appendChild(selection);
  const shelf = el('section', 'house-section');
  shelf.id = 'creator-shelf';
  workspaceBody.appendChild(shelf);
  creatorV2RenderSelection();
  creatorV2RenderShelf();
}
function creatorV2RenderSelection() {
  const host = $('#creator-selected');
  if (!host) return;
  const s = creatorV2State();
  clear(host);
  host.appendChild(el('p', 'muted tiny', s.selected.length + '/8 local source lines selected. Unselected repository content stays outside the pack.'));
  s.selected.forEach((item, index) => {
    const row = el('div', 'creator-selected-row');
    row.appendChild(el('span', '', item.root_id + ':' + item.repo_path + '/' + item.source_path + '#L' + item.line + ' — ' + item.snippet));
    const remove = el('button', 'quiet-button', 'Remove');
    remove.type = 'button';
    remove.addEventListener('click', () => {
      s.selected.splice(index, 1);
      s.preview = null;
      creatorV2RenderSelection();
    });
    row.appendChild(remove);
    host.appendChild(row);
  });
  const actions = el('div', 'terminal-actions');
  const preview = el('button', 'action-button', 'Preview selected source pack');
  preview.type = 'button';
  preview.disabled = !s.selected.length;
  const clearSelection = el('button', 'quiet-button', 'Clear selected lines');
  clearSelection.type = 'button';
  clearSelection.addEventListener('click', () => {
    s.selected = [];
    s.preview = null;
    creatorV2RenderSelection();
  });
  actions.append(preview, clearSelection);
  host.appendChild(actions);
  const result = el('div', 'creator-pack-preview');
  host.appendChild(result);
  preview.addEventListener('click', async () => {
    clear(result);
    try {
      const pack = await creatorV2Write('/api/creator/packs/preview', { selections: s.selected });
      s.preview = pack;
      result.append(
        el('div', 'eyebrow', 'REVIEW ALL ' + pack.source_count + ' SOURCE LINES'),
        el('div', 'muted tiny', 'Pack SHA-256: ' + pack.pack_sha256)
      );
      pack.sources.forEach(source => {
        const row = el('article', 'creator-preview-source');
        row.append(
          el('div', 'repo-name', source.root_id + ':' + source.repo_path + '/' + source.source_path + '#L' + source.line_start),
          el('pre', 'raw-carrier', source.excerpt),
          el('div', 'muted tiny', 'File SHA-256: ' + source.file_sha256 + (source.worktree_dirty ? ' · dirty working tree' : ' · clean at selection'))
        );
        result.appendChild(row);
      });
      result.appendChild(el('p', 'muted tiny', 'Excerpts are from current local worktrees, not verified frozen Git commits. Review for private information before saving.'));
      const save = el('button', 'action-button', 'Save exactly this pack locally');
      save.type = 'button';
      save.addEventListener('click', async () => {
        save.disabled = true;
        try {
          const saved = await creatorV2Write('/api/creator/packs', {
            selections: s.selected, expected_pack_sha256: pack.pack_sha256,
          });
          s.pack = await api('/api/creator/packs/' + saved.id);
          s.draft = null;
          s.selected = [];
          s.preview = null;
          await creatorV2Load();
          creatorV2RenderSelection();
        } catch (error) {
          creatorV2Message(result, error.message || String(error), true);
          save.disabled = false;
        }
      });
      result.appendChild(save);
    } catch (error) {
      s.preview = null;
      creatorV2Message(result, error.message || String(error), true);
    }
  });
}
async function creatorV2Load() {
  const s = creatorV2State();
  const results = await Promise.all([api('/api/creator/packs'), api('/api/creator/drafts')]);
  s.packs = results[0].packs;
  s.drafts = results[1].drafts;
  if (state.view === 'creator') creatorV2RenderShelf();
}
function creatorV2RenderShelf() {
  const host = $('#creator-shelf');
  if (!host) return;
  const s = creatorV2State();
  clear(host);
  host.appendChild(el('div', 'section-heading', 'LOCAL DRAFT SHELF / NOT PROJECT CANON'));

  const packs = el('article', 'card creator-shelf-card');
  packs.appendChild(el('h2', '', 'Saved source packs'));
  if (!s.packs.length) packs.appendChild(el('p', 'muted', 'No saved packs yet.'));
  s.packs.forEach(item => {
    const button = el('button', 'quiet-button creator-source-button', 'Use pack #' + item.id + ' · ' + item.source_count + ' lines · ' + item.pack_sha256.slice(0, 12));
    button.type = 'button';
    button.addEventListener('click', async () => {
      try {
        s.pack = await api('/api/creator/packs/' + item.id);
        s.draft = null;
        creatorV2RenderShelf();
      } catch (error) { creatorV2Message(packs, error.message || String(error), true); }
    });
    packs.appendChild(button);
  });
  host.appendChild(packs);

  const drafts = el('article', 'card creator-shelf-card');
  drafts.appendChild(el('h2', '', 'Working drafts'));
  if (!s.drafts.length) drafts.appendChild(el('p', 'muted', 'No local drafts yet.'));
  s.drafts.forEach(item => {
    const button = el('button', 'quiet-button creator-source-button', 'Open draft #' + item.id + ' · r' + item.revision + ' · ' + item.title);
    button.type = 'button';
    button.addEventListener('click', async () => {
      try {
        const loaded = await Promise.all([
          api('/api/creator/drafts/' + item.id),
          api('/api/creator/packs/' + item.pack_id),
        ]);
        s.draft = loaded[0];
        s.pack = loaded[1];
        creatorV2RenderShelf();
      } catch (error) { creatorV2Message(drafts, error.message || String(error), true); }
    });
    drafts.appendChild(button);
  });
  host.appendChild(drafts);

  const editor = el('article', 'card creator-editor');
  editor.appendChild(el('h2', '', 'Write in HOUSE'));
  if (!s.pack) {
    editor.appendChild(el('p', 'muted', 'Choose a saved source pack to start drafting.'));
    host.appendChild(editor);
    return;
  }
  const pack = s.pack;
  editor.appendChild(el('div', 'muted tiny', 'Working from source pack #' + pack.id + ' · ' + pack.pack_sha256));
  pack.sources.forEach(source => editor.appendChild(el('div', 'muted tiny',
    source.root_id + ':' + source.repo_path + '/' + source.source_path + '#L' + source.line_start
  )));
  if (s.draft) editor.appendChild(el('div', 'muted tiny', 'Draft #' + s.draft.id + ' · revision ' + s.draft.revision + ' · each save appends a revision'));
  const form = el('form', 'creator-edit-form');
  const title = el('input'); title.required = true; title.maxLength = 160; title.placeholder = 'Working title';
  title.setAttribute('aria-label', 'Draft title'); title.value = s.draft?.title || '';
  const kind = el('select'); kind.setAttribute('aria-label', 'Draft format');
  ['lyric', 'podcast', 'post', 'brief', 'other'].forEach(name => {
    const option = el('option', '', name); option.value = name; kind.appendChild(option);
  });
  kind.value = s.draft?.kind || 'lyric';
  const body = el('textarea', 'creator-draft-body'); body.rows = 12; body.maxLength = 32768;
  body.required = true; body.placeholder = 'Write the draft here…';
  body.setAttribute('aria-label', 'Draft body'); body.value = s.draft?.body || '';
  const assumptions = el('textarea'); assumptions.rows = 3; assumptions.maxLength = 4000;
  assumptions.placeholder = 'Creative assumptions or interpretation (optional)';
  assumptions.setAttribute('aria-label', 'Creative assumptions'); assumptions.value = s.draft?.assumptions || '';
  const gaps = el('textarea'); gaps.rows = 3; gaps.maxLength = 4000;
  gaps.placeholder = 'Unresolved questions and gaps (optional)';
  gaps.setAttribute('aria-label', 'Unresolved gaps'); gaps.value = s.draft?.gaps || '';
  const save = el('button', 'action-button', 'Save new local revision'); save.type = 'submit';
  const fresh = el('button', 'quiet-button', 'Start another draft from this pack'); fresh.type = 'button';
  fresh.addEventListener('click', () => { s.draft = null; creatorV2RenderShelf(); });
  const feedback = el('div', 'creator-feedback');
  form.append(title, kind, body, assumptions, gaps, save, fresh, feedback);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    save.disabled = true;
    const payload = {
      pack_id: pack.id, expected_revision: s.draft?.revision || 0,
      title: title.value, kind: kind.value, body: body.value,
      assumptions: assumptions.value, gaps: gaps.value,
    };
    const path = s.draft ? '/api/creator/drafts/' + s.draft.id + '/revisions' : '/api/creator/drafts';
    try {
      const saved = await creatorV2Write(path, payload);
      s.draft = await api('/api/creator/drafts/' + saved.id);
      await creatorV2Load();
      creatorV2RenderShelf();
    } catch (error) {
      creatorV2Message(feedback, (error.message || String(error)) + ' · Unsaved text remains in this editor.', true);
      save.disabled = false;
    }
  });
  editor.appendChild(form);
  if (s.draft) {
    const copy = el('button', 'quiet-button', 'Copy draft + source references (manual handoff)');
    copy.type = 'button';
    const result = el('div', 'creator-feedback');
    copy.addEventListener('click', async () => {
      const refs = pack.sources.map(source =>
        source.root_id + ':' + source.repo_path + '/' + source.source_path + '#L' + source.line_start
        + ' · file SHA-256 ' + source.file_sha256
        + (source.worktree_dirty ? ' · dirty at selection' : ' · clean at selection')
      ).join('\n');
      const handoff = [
        'CREATOR DESK / HUMAN-SELECTED LOCAL DRAFT',
        'Title: ' + s.draft.title,
        'Format: ' + s.draft.kind,
        'Local draft #' + s.draft.id + ', revision ' + s.draft.revision,
        'Source pack #' + pack.id + ' · ' + pack.pack_sha256,
        'Selected local source references:\n' + refs,
        'Creative assumptions: ' + (s.draft.assumptions || '(none declared)'),
        'Unresolved gaps: ' + (s.draft.gaps || '(none declared)'),
        'Draft text:\n' + s.draft.body,
        'Local draft only; not a publication receipt or project canon.',
      ].join('\n\n');
      clear(result);
      if (navigator.clipboard?.writeText) {
        try {
          await navigator.clipboard.writeText(handoff);
          creatorV2Message(result, 'Copied by explicit request. Nothing was published or sent to a model.', false);
          return;
        } catch (_) { /* manual fallback */ }
      }
      result.appendChild(el('p', 'muted', 'Clipboard unavailable; select and copy the handoff manually.'));
      const manual = el('textarea', 'handoff-manual'); manual.readOnly = true;
      manual.value = handoff; result.appendChild(manual);
      manual.focus(); manual.select();
    });
    editor.append(copy, result);
  }
  host.appendChild(editor);
}
