// BRANCH-HARBOR-003. Session-memory preview only. No remote fetch or project writes.
// Manifests are foreign data and their reported HOLD/CI state is not verified here.
let harborDraftText = '';
let harborPreview = null;

function branchHarborCard(parent) {
  const section = el('section', 'card branch-harbor-shelf');
  section.append(
    el('div', 'eyebrow', 'FREEPORT 006 / FOREIGN BRANCH CARGO'),
    el('h2', '', 'The Branch Harbor'),
    el('p', 'muted', 'Paste an explicitly selected FREEPORT 006 synthetic public manifest. The original Git branches stay elsewhere. This desk does not fetch, execute, merge, select, or admit code. HOLD is always manifest-reported until verified independently.')
  );
  const row = el('div', 'branch-harbor-ports');
  for (const [icon, text] of [
    ['01 / DOCK', 'Pinned foreign commits'],
    ['02 / INSPECT', 'Source-bound unrun proposal'],
    ['03 / TRACE', 'Free Graph seed'],
    ['04 / GATE', 'Independent receiver review'],
  ]) {
    const cell = el('div', 'branch-harbor-port');
    cell.append(el('div', 'eyebrow', icon), el('div', 'repo-name', text));
    row.append(cell);
  }
  section.append(row);
  const instructions = el('p', 'muted tiny',
    'Local session memory only. Use the public synthetic manifest from FREEPORT 006 CI; never paste private WITNESS material, tokens, raw source files or consent-restricted metadata.');
  const field = el('textarea', 'branch-harbor-manifest');
  field.rows = 5;
  field.maxLength = 16384;
  field.value = harborDraftText;
  field.placeholder = '{ "schema": "freeport.branch-graft/v0", "version": "006", … }';
  field.setAttribute('aria-label', 'Paste synthetic Freeport 006 manifest JSON');
  const control = el('div', 'branch-harbor-actions');
  const view = el('button', 'action-button', 'Inspect manifest and ancestry');
  view.type = 'button';
  const clearButton = el('button', 'quiet-button', 'Clear local harbor');
  clearButton.type = 'button';
  const status = el('div', 'muted tiny', 'No Freeport cargo manifest inspected this session.');
  const out = el('div', 'branch-harbor-result');
  field.addEventListener('input', () => {
    harborDraftText = field.value;
    harborPreview = null;
    clear(out);
    status.textContent = 'Manifest changed. Reinspect before viewing any claims.';
  });
  clearButton.addEventListener('click', () => {
    harborDraftText = '';
    harborPreview = null;
    field.value = '';
    clear(out);
    status.textContent = 'Cleared from this local browser session.';
  });
  view.addEventListener('click', async () => {
    view.disabled = true;
    status.textContent = 'Inspecting a bounded, untrusted manifest locally…';
    try {
      const token = state.bootstrap?.session_token;
      if (!token) throw new Error('Local Workbench session token unavailable');
      const result = await api('/api/branches/freeport/preview', {
        method: 'POST',
        body: harborDraftText,
        headers: {'Content-Type': 'application/json', 'x-workbench-session': token},
      });
      harborPreview = result;
      drawHarborProjection(out, result);
      status.textContent = 'Projection generated from unverified manifest fields, not native Freeport cold proof.';
    } catch (error) {
      harborPreview = null;
      clear(out);
      status.textContent = String(error.message || error);
    } finally { view.disabled = false; }
  });
  control.append(view, clearButton);
  section.append(instructions, field, control, status, out);
  parent.append(section);
  if (harborPreview) drawHarborProjection(out, harborPreview);
}

function drawHarborProjection(target, data) {
  clear(target);
  const summary = el('div', 'branch-harbor-boundary');
  summary.append(
    el('div', 'eyebrow', 'REVIEW ONLY / FREE GRAPH v0 SEED'),
    el('div', 'repo-name', data.proposal_branch),
    el('p', 'notice',
      'HOLD (manifest-reported) · source bytes NOT verified here · no branch created · no canon/KEEP/ADMIT/merge authority')
  );
  const sources = el('div', 'branch-harbor-source-grid');
  const localRefs = branchDeckSnapshot?.branches || [];
  for (const source of data.sources) {
    const card = el('div', 'branch-harbor-source');
    const local = localRefs.some(ref =>
      ref.repo_name?.toLowerCase() === source.repository.split('/')[1].toLowerCase()
      && ref.name === source.branch_hint && ref.commit === source.commit);
    card.append(
      el('div', 'eyebrow', 'FOREIGN / SOURCE-DECLARED'),
      el('div', 'repo-name', source.repository + ' / ' + source.branch_hint),
      el('div', 'repo-meta', 'Commit claim: ' + source.commit),
      el('div', 'repo-meta', 'Selected file: ' + source.path),
      el('div', 'muted tiny', local
        ? 'Exact locally cached ref observed; file bytes not authenticated by this desk.'
        : 'Exact local ref not observed in present Branch Deck inventory; may be in another checkout.')
    );
    sources.append(card);
  }
  const graph = data.graph;
  const relations = el('div', 'branch-harbor-relations');
  relations.append(el('div', 'repo-name', 'Free Graph / ancestry and test questions'),
    el('div', 'muted tiny', graph.packet_id + ' · seed-only · unresolved Task World Cut'));
  const names = new Map(graph.nodes.map(n => [n.id, n.label]));
  for (const edge of graph.links) {
    const item = el('div', 'branch-harbor-relation');
    item.append(
      el('span', 'repo-meta', names.get(edge.from) || 'unknown source'),
      el('strong', 'branch-harbor-verb', edge.verb),
      el('span', 'repo-meta', names.get(edge.to) || 'unknown target'),
      el('div', 'muted tiny', edge.qualifier)
    );
    relations.append(item);
  }
  const exportButton = el('button', 'quiet-button', 'Export pointer-only Free Graph seed');
  exportButton.type = 'button';
  exportButton.addEventListener('click', () => {
    // Manual disclosure action; packet has only bounded refs, not foreign bytes.
    const text = JSON.stringify(graph, null, 2) + '\n';
    const url = URL.createObjectURL(new Blob([text], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'freeport-006-free-graph.seed.json';
    link.click();
    URL.revokeObjectURL(url);
  });
  summary.append(sources, relations,
    el('p', 'muted tiny', 'The tests edge records only a reported synthetic probe. No Free Graph constitutes edge is minted: destination-local authority has not entered this Workbench preview.'),
    exportButton);
  target.append(summary);
}
