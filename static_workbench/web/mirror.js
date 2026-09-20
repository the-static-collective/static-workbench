/* MIRROR-001: selected demo element -> reversible visual overrides -> reviewed CSS patch. */
async function renderMirror() {
  state.view = 'mirror'; syncNav('mirror');
  setWorkspace('MIRROR / experimental', 'Visual editing proof');
  clear(workspaceBody);
  const panel = el('section', 'card');
  panel.append(el('div', 'eyebrow', 'ONE OWNED SURFACE / NO EXTERNAL PROJECT WRITES'),
    el('h2', '', 'Inspect a live demo. Edit its appearance. Review the source delta.'),
    el('p', 'muted', 'This fixture is served from the local Workbench. Select its card inside the preview. No other app, project or repo is editable in MIRROR-001.'));
  const layout = el('div', 'mirror-layout');
  const frame = el('iframe', 'mirror-frame');
  frame.title = 'MIRROR owned demonstration application';
  frame.setAttribute('sandbox', 'allow-same-origin');
  frame.src = '/api/mirror/demo';
  const inspector = el('form', 'card mirror-inspector');
  const heading = el('h3', '', 'Inspector');
  const selected = el('div', 'muted tiny', 'Click the card in the live preview to select it.');
  const widthLabel = el('label', '', 'Card width (220–600 px)');
  const width = el('input'); width.type = 'range'; width.min = '220'; width.max = '600'; width.step = '1';
  const widthValue = el('output');
  const colorLabel = el('label', '', 'Accent color');
  const accent = el('input'); accent.type = 'color';
  const review = el('button', 'action-button', 'Preview source patch'); review.type = 'submit';
  const apply = el('button', 'quiet-button', 'Apply reviewed patch to demo source');
  apply.type = 'button'; apply.disabled = true;
  const reset = el('button', 'quiet-button', 'Discard visual overrides'); reset.type = 'button';
  const feedback = el('div', 'muted tiny');
  const diff = el('pre', 'code-preview'); diff.textContent = 'No source patch proposed.';
  inspector.append(heading, selected, widthLabel, width, widthValue, colorLabel, accent, review, apply, reset, feedback);
  layout.append(frame, inspector);
  panel.append(layout, el('h3', '', 'Proposed source delta'), diff);
  workspaceBody.appendChild(panel);
  let observed = null;
  let reviewed = null;
  let hasSelection = false;
  for (const element of [width, accent, review, reset]) element.disabled = true;
  function paint() {
    widthValue.textContent = width.value + ' px';
    const root = frame.contentDocument?.documentElement;
    if (!root || !hasSelection) return;
    root.style.setProperty('--mirror-card-width', width.value + 'px');
    root.style.setProperty('--mirror-accent', accent.value.toLowerCase());
  }
  function invalidate() {
    reviewed = null;
    apply.disabled = true;
    diff.textContent = 'Visual override only — review a new patch to edit source.';
    feedback.textContent = 'Source unchanged.';
  }
  function chooseCard(event) {
    const target = event.target.closest('[data-mirror-target="demo-card"]');
    if (!target) return;
    hasSelection = true;
    target.style.outline = '3px dashed #eeb86c';
    selected.textContent = 'Selected: demo-card · Workbench-owned CSS tokens';
    for (const element of [width, accent, review, reset]) element.disabled = false;
    paint();
  }
  frame.addEventListener('load', () => {
    if (!frame.contentDocument) {
      selected.textContent = 'Preview unavailable: origin or iframe policy prevented inspection.';
      return;
    }
    frame.contentDocument.addEventListener('click', chooseCard);
    if (hasSelection) {
      const card = frame.contentDocument.querySelector('[data-mirror-target="demo-card"]');
      if (card) { card.style.outline = '3px dashed #eeb86c'; paint(); }
    }
  });
  try {
    observed = await api('/api/mirror/state');
    if (state.view !== 'mirror') return;
    width.value = String(observed.card_width);
    accent.value = observed.accent;
    widthValue.textContent = width.value + ' px';
    feedback.textContent = 'Observed demo CSS SHA-256: ' + observed.source_sha256;
  } catch (error) {
    selected.textContent = error.message;
    frame.src = 'about:blank';
    return;
  }
  width.addEventListener('input', () => { invalidate(); paint(); });
  accent.addEventListener('input', () => { invalidate(); paint(); });
  reset.addEventListener('click', () => {
    width.value = String(observed.card_width);
    accent.value = observed.accent;
    invalidate(); paint();
  });
  inspector.addEventListener('submit', async event => {
    event.preventDefault();
    if (!hasSelection || !observed) return;
    const patch = {
      expected_source_sha256: observed.source_sha256,
      card_width: Number(width.value), accent: accent.value.toLowerCase(),
    };
    review.disabled = true;
    try {
      const result = await api('/api/mirror/preview', {
        method: 'POST', headers: { 'x-workbench-session': state.bootstrap.session_token },
        body: JSON.stringify(patch),
      });
      reviewed = result.changed ? {patch, result} : null;
      apply.disabled = !reviewed;
      diff.textContent = result.diff || 'No difference from the observed source.';
      feedback.textContent = result.changed ?
        'Reviewed proposal: ' + result.after_sha256 + ' · no source modification yet.' : 'No change to apply.';
    } catch (error) {
      reviewed = null; apply.disabled = true; feedback.textContent = error.message;
    } finally { review.disabled = false; }
  });
  apply.addEventListener('click', async () => {
    if (!reviewed) return;
    apply.disabled = true;
    try {
      const receipt = await api(
        '/api/mirror/apply?expected_after_sha256=' + encodeURIComponent(reviewed.result.after_sha256),
        { method: 'POST', headers: { 'x-workbench-session': state.bootstrap.session_token },
          body: JSON.stringify(reviewed.patch) },
      );
      observed = receipt;
      reviewed = null;
      diff.textContent = 'Applied to Workbench-owned demo.css. Before: ' + receipt.before_sha256 +
        '\nAfter:  ' + receipt.source_sha256 + '\nReopen the inspector to make another change.';
      feedback.textContent = 'Source written after explicit approval; independent app repositories unchanged.';
      frame.src = '/api/mirror/demo?version=' + receipt.source_sha256;
      if (typeof loadEvents === 'function') loadEvents().catch(() => {});
    } catch (error) { feedback.textContent = error.message; reviewed = null; }
  });
}
