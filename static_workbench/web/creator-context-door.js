/* CREATOR-CONTEXT-DOOR-001: explicit source selection -> inert local draft
 * routing preview. Never reads a checkout, invokes Toaster, executes a plan,
 * silently writes a draft, or treats a saved snapshot as current source truth.
 */
function creatorContextProposal(pack, selectedIndices, response) {
  if (!pack || !Number.isSafeInteger(pack.id) || pack.id < 1 ||
      typeof pack.pack_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(pack.pack_sha256) ||
      !Array.isArray(pack.sources) || !pack.sources.length || pack.sources.length > 8) {
    throw new Error('Choose a valid saved source pack first.');
  }
  if (!['follow', 'contrast'].includes(response)) throw new Error('Unknown composition direction.');
  if (!Array.isArray(selectedIndices) || !selectedIndices.length ||
      selectedIndices.length > pack.sources.length ||
      new Set(selectedIndices).size !== selectedIndices.length ||
      selectedIndices.some(index => !Number.isInteger(index) || index < 0 || index >= pack.sources.length)) {
    throw new Error('Choose one or more distinct source lines from this pack.');
  }
  const sends = selectedIndices.slice().sort((a, b) => a - b).map(index => {
    const source = pack.sources[index];
    if (!source || !Number.isSafeInteger(source.line_start) || source.line_start < 1 ||
        !['root_id', 'repo_path', 'source_path'].every(key =>
          typeof source[key] === 'string' && source[key].length > 0 && source[key].length <= 1024) ||
        typeof source.file_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(source.file_sha256)) {
      throw new Error('Saved source details are incomplete; this composition cannot be prepared.');
    }
    return Object.freeze({
      index, source_ref: source.root_id + ':' + source.repo_path + '/' +
        source.source_path + '#L' + source.line_start,
      file_sha256: source.file_sha256, target: 'local-draft',
      scope: 'draft-idea', response, influence: 'declared-creative-proposal',
    });
  });
  const chosen = new Set(selectedIndices);
  const ignored = pack.sources.map((_, index) => index).filter(index => !chosen.has(index));
  return Object.freeze({
    policy: 'creator-context-door.v0', pack_id: pack.id,
    pack_sha256: pack.pack_sha256, sends: Object.freeze(sends),
    ignored: Object.freeze(ignored), status: 'preview-only-not-saved',
  });
}

function creatorContextDoor(pack, desk, editorFields) {
  const section = el('section', 'creator-context-door');
  const heading = el('h3', '', 'Shape this draft with your saved material');
  section.append(heading, el('p', 'muted',
    'Choose which saved lines to draw from. See two different ways to use them; neither changes the original material.'));
  if (desk.draft) {
    section.appendChild(el('p', 'muted tiny',
      'This composer starts a new draft only. Your open draft and its revisions remain unchanged.'));
    return section;
  }
  const selectors = [];
  pack.sources.forEach((source, index) => {
    const label = el('label', 'creator-context-source');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.setAttribute('aria-label', 'Use saved source line ' + (index + 1));
    selectors.push(checkbox);
    const text = el('span', '', source.root_id + ':' + source.repo_path + '/' +
      source.source_path + '#L' + source.line_start);
    label.append(checkbox, text);
    section.appendChild(label);
  });
  const actions = el('div', 'creator-actions');
  const follow = el('button', 'quiet-button', 'Build from these lines');
  const contrast = el('button', 'quiet-button', 'Try a contrasting direction');
  follow.type = 'button'; contrast.type = 'button';
  actions.append(follow, contrast);
  section.appendChild(actions);
  const preview = el('div', 'creator-context-preview');
  preview.setAttribute('aria-live', 'polite');
  section.appendChild(preview);
  function invalidate() {
    clear(preview);
    preview.appendChild(el('p', 'muted tiny',
      'Selection changed. Preview a new composition before adding anything to your draft.'));
  }
  selectors.forEach(checkbox => checkbox.addEventListener('change', invalidate));
  function show(response) {
    clear(preview);
    let plan;
    try {
      plan = creatorContextProposal(pack,
        selectors.flatMap((checkbox, index) => checkbox.checked ? [index] : []), response);
    } catch (error) {
      creatorV2Message(preview, error.message || String(error), true);
      return;
    }
    preview.appendChild(el('h3', '',
      response === 'follow' ? 'Build from your selected lines' : 'Explore a contrasting interpretation'));
    preview.appendChild(el('p', 'muted',
      response === 'follow'
        ? 'Use the selected lines as starting material for your writing.'
        : 'Use the selected lines as material to question, contrast, or respond to in your writing.'));
    preview.appendChild(el('div', 'muted tiny',
      'From: saved pack #' + plan.pack_id + ' · ' + plan.pack_sha256));
    preview.appendChild(el('div', 'muted tiny',
      'To: this local draft only · no video or external tool will be started.'));
    plan.sends.forEach(send => {
      preview.appendChild(el('div', 'muted tiny',
        'Will consider: ' + send.source_ref + ' · response: ' + send.response));
    });
    preview.appendChild(el('div', 'muted tiny',
      plan.ignored.length + ' other saved source line(s) not selected for this proposal.'));
    preview.appendChild(el('p', 'muted tiny',
      'These are historical saved excerpts, not a check of the current source files. Your original files remain unchanged. No context has been sent or saved.'));
    const apply = el('button', 'action-button', 'Use this direction in my new draft');
    apply.type = 'button';
    const status = el('div', 'creator-context-status');
    apply.addEventListener('click', () => {
      if (desk.draft || editorFields.assumptions.value.trim()) {
        creatorV2Message(status,
          'This draft already has creative notes. Nothing was replaced; clear them yourself if you want to apply this proposal.', true);
        apply.disabled = true;
        return;
      }
      const message = [
        'Creative direction (proposal only; source material not independently rechecked):',
        response === 'follow'
          ? 'Build from the explicitly selected saved excerpts.'
          : 'Explore a contrasting interpretation of the explicitly selected saved excerpts.',
        'Saved source pack #' + plan.pack_id + ' · ' + plan.pack_sha256,
        ...plan.sends.map(send => 'Selected source: ' + send.source_ref +
          ' · file digest at save: ' + send.file_sha256),
        'Other saved lines not selected: ' + plan.ignored.length + '.',
        'Sources remain unchanged. This is not project authority or a claim that a draft has been saved.'
      ].join('\n');
      if (message.length > editorFields.assumptions.maxLength) {
        creatorV2Message(status, 'Source references exceed this editor’s note limit. No text was changed.', true);
        return;
      }
      editorFields.assumptions.value = message;
      editorFields.body.focus();
      creatorV2Message(status,
        'Creative direction added to this editor. Write your draft and choose Save when you are ready; nothing has been saved or sent yet.', false);
      apply.disabled = true;
    });
    preview.append(apply, status);
  }
  follow.addEventListener('click', () => show('follow'));
  contrast.addEventListener('click', () => show('contrast'));
  return section;
}
