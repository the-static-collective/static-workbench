/* Return Desk v0.1 — local, human-declared note → session → checkpoint. */
const returnDeskState = { notes: [], sessions: [], selectedNote: null, selectedSession: null };

async function returnDeskWrite(path, body) {
  return api(path, {
    method: 'POST',
    headers: { 'X-Workbench-Session': state.bootstrap.session_token },
    body: JSON.stringify(body),
  });
}
function returnDeskField(form, caption, multiline, max, value = '', required = false) {
  const label = el('label', 'return-field');
  label.appendChild(el('span', 'muted tiny', caption));
  const field = el(multiline ? 'textarea' : 'input');
  field.maxLength = max;
  field.required = required;
  field.value = value;
  if (multiline) field.rows = 3;
  label.appendChild(field);
  form.appendChild(label);
  return field;
}
function returnDeskError(host, error) {
  host.textContent = error.message || String(error);
  host.className = 'notice error';
}
function returnDeskStamp(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}
async function returnDeskOpenSession(id) {
  returnDeskState.selectedSession = await api('/api/return/sessions/' + id);
  returnDeskState.selectedNote = returnDeskState.selectedSession.note;
  returnDeskRender();
}
async function returnDeskOpenNote(id) {
  returnDeskState.selectedNote = await api('/api/return/notes/' + id);
  returnDeskState.selectedSession = null;
  returnDeskRender();
}
async function returnDeskLoad() {
  const [notes, sessions] = await Promise.all([
    api('/api/return/notes'), api('/api/return/sessions'),
  ]);
  returnDeskState.notes = notes.notes;
  returnDeskState.sessions = sessions.sessions;
  const selected = returnDeskState.selectedSession?.id || (!returnDeskState.selectedNote ? sessions.sessions[0]?.id : null);
  if (selected) {
    returnDeskState.selectedSession = await api('/api/return/sessions/' + selected);
    returnDeskState.selectedNote = returnDeskState.selectedSession.note;
  } else if (returnDeskState.selectedNote) {
    returnDeskState.selectedNote = await api('/api/return/notes/' + returnDeskState.selectedNote.id);
  }
  returnDeskRender();
}
function returnDeskRender() {
  state.view = 'return';
  syncNav('return');
  setWorkspace('Return Desk', 'Write · Carry · Return');
  clear(workspaceBody);
  const header = el('section', 'card return-header');
  header.append(
    el('div', 'eyebrow', 'HOUSE-OWNED / LOCAL'),
    el('h2', '', 'A note becomes a returnable work session'),
    el('p', 'muted', 'Original text is immutable after saving. Margins and carry statements remain separate. Each checkpoint appends a new receipt; it does not edit a repository, GOATnote, or project-native history.'),
  );
  workspaceBody.appendChild(header);

  const create = el('section', 'card return-panel');
  create.appendChild(el('h2', '', '1 · Capture a new note'));
  const form = el('form', 'return-form');
  const title = returnDeskField(form, 'Title', false, 160, '', true);
  const raw = returnDeskField(form, 'RAW · original writing', true, 20000, '', true);
  raw.rows = 6;
  const margin = returnDeskField(form, 'Margin · context or later questions (optional)', true, 4000);
  const carry = returnDeskField(form, 'Identity carry · what matters to preserve (optional)', true, 4000);
  const save = el('button', 'action-button', 'Save original note locally');
  save.type = 'submit';
  const feedback = el('div');
  form.append(save, feedback);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    save.disabled = true;
    try {
      const note = await returnDeskWrite('/api/return/notes', {
        title: title.value, raw_text: raw.value, margin: margin.value, carry: carry.value,
      });
      returnDeskState.selectedNote = note;
      returnDeskState.selectedSession = null;
      await returnDeskLoad();
      await loadEvents();
    } catch (error) {
      returnDeskError(feedback, error);
      save.disabled = false;
    }
  });
  create.appendChild(form);
  workspaceBody.appendChild(create);

  const history = el('section', 'card return-panel');
  history.appendChild(el('h2', '', '2 · Recover an existing session'));
  if (!returnDeskState.sessions.length) history.appendChild(el('p', 'muted', 'No sessions yet. Save a note, then open its first session.'));
  returnDeskState.sessions.forEach(item => {
    const button = el('button', 'quiet-button return-history-button',
      '#' + item.id + ' · ' + item.note_title + ' · checkpoint ' + item.revision + ' · ' + item.next_step);
    button.type = 'button';
    button.addEventListener('click', () => returnDeskOpenSession(item.id).catch(showError));
    history.appendChild(button);
  });
  history.appendChild(el('h3', '', 'Saved notes'));
  if (!returnDeskState.notes.length) history.appendChild(el('p', 'muted', 'No notes saved.'));
  returnDeskState.notes.forEach(note => {
    const button = el('button', 'quiet-button return-history-button', '#' + note.id + ' · ' + note.title);
    button.type = 'button';
    button.addEventListener('click', () => returnDeskOpenNote(note.id).catch(showError));
    history.appendChild(button);
  });
  workspaceBody.appendChild(history);

  const note = returnDeskState.selectedNote;
  if (!note) return;
  const original = el('section', 'card return-panel');
  original.append(
    el('div', 'eyebrow', 'SELECTED ORIGINAL · NOTE #' + note.id),
    el('h2', '', note.title),
    el('div', 'muted tiny', returnDeskStamp(note.created_at) + ' · SHA-256 ' + note.sha256),
    el('h3', '', 'RAW · preserved'),
    el('pre', 'raw-carrier return-raw', note.raw_text),
    el('h3', '', 'Margin · separate'),
    el('pre', 'raw-carrier return-raw', note.margin || '(none declared)'),
    el('h3', '', 'Identity carry · separate'),
    el('pre', 'raw-carrier return-raw', note.carry || '(none declared)'),
  );
  workspaceBody.appendChild(original);

  const newSession = el('section', 'card return-panel');
  newSession.appendChild(el('h2', '', '3 · Open a work session from this exact note'));
  const sessionForm = el('form', 'return-form');
  const project = returnDeskField(sessionForm, 'Project label · human-declared, not inspected (optional)', false, 160);
  const intention = returnDeskField(sessionForm, 'Intention', true, 4000, '', true);
  const next = returnDeskField(sessionForm, 'Next physical action', true, 4000, '', true);
  const unresolved = returnDeskField(sessionForm, 'Unresolved / not yet claimed', true, 4000);
  const open = el('button', 'action-button', 'Open session and save first checkpoint');
  open.type = 'submit';
  const sessionFeedback = el('div');
  sessionForm.append(open, sessionFeedback);
  sessionForm.addEventListener('submit', async event => {
    event.preventDefault();
    open.disabled = true;
    try {
      const saved = await returnDeskWrite('/api/return/sessions', {
        note_id: note.id, expected_note_sha256: note.sha256,
        project: project.value, intention: intention.value,
        next_step: next.value, unresolved: unresolved.value,
      });
      await returnDeskOpenSession(saved.id);
      await returnDeskLoad();
      await loadEvents();
    } catch (error) {
      returnDeskError(sessionFeedback, error);
      open.disabled = false;
    }
  });
  newSession.appendChild(sessionForm);
  workspaceBody.appendChild(newSession);

  const session = returnDeskState.selectedSession;
  if (!session) return;
  const active = el('section', 'card return-panel');
  active.append(
    el('div', 'eyebrow', 'WORK SESSION #' + session.id + ' · PROJECT LABEL: ' + (session.project || '(none)')),
    el('h2', '', 'Resume where you left off'),
    el('p', 'muted', 'Intention: ' + session.intention),
    el('div', 'muted tiny', 'Linked original SHA-256 ' + session.note_sha256),
    el('h3', '', 'Current next action'),
    el('pre', 'raw-carrier return-raw', session.latest.next_step),
    el('h3', '', 'Unresolved'),
    el('pre', 'raw-carrier return-raw', session.latest.unresolved || '(none declared)'),
  );
  const checkpointForm = el('form', 'return-form');
  const changed = returnDeskField(checkpointForm, 'What happened since the last checkpoint?', true, 4000);
  const future = returnDeskField(checkpointForm, 'Next action on return', true, 4000, session.latest.next_step, true);
  const fog = returnDeskField(checkpointForm, 'What remains unresolved?', true, 4000, session.latest.unresolved);
  const checkpointSave = el('button', 'action-button', 'Append checkpoint · revision ' + (session.latest.revision + 1));
  checkpointSave.type = 'submit';
  const checkFeedback = el('div');
  checkpointForm.append(checkpointSave, checkFeedback);
  checkpointForm.addEventListener('submit', async event => {
    event.preventDefault();
    checkpointSave.disabled = true;
    try {
      await returnDeskWrite('/api/return/sessions/' + session.id + '/checkpoints', {
        expected_revision: session.latest.revision, changed: changed.value,
        next_step: future.value, unresolved: fog.value,
      });
      await returnDeskOpenSession(session.id);
      await returnDeskLoad();
      await loadEvents();
    } catch (error) {
      returnDeskError(checkFeedback, error);
      checkpointSave.disabled = false;
    }
  });
  active.appendChild(checkpointForm);
  const chain = el('section', 'return-checkpoint-chain');
  chain.appendChild(el('h3', '', 'Append-only checkpoints / local receipts'));
  session.checkpoints.slice().reverse().forEach(item => {
    const record = el('article', 'return-checkpoint');
    record.append(
      el('div', 'eyebrow', 'REVISION ' + item.revision + ' · ' + returnDeskStamp(item.created_at)),
      el('p', '', 'Changed: ' + (item.changed || '(initial hold)')),
      el('p', '', 'Next: ' + item.next_step),
      el('p', '', 'Unresolved: ' + (item.unresolved || '(none declared)')),
      el('div', 'muted tiny return-digest', 'SHA-256 ' + item.sha256 + ' · previous ' + (item.previous_sha256 || '(root)')),
    );
    chain.appendChild(record);
  });
  active.appendChild(chain);
  workspaceBody.appendChild(active);
}
