/* Human-pasted Founder Node inspection: no auto-fetch, persistence or execution. */
function renderCompositionInspection() {
  state.view = 'composition'; syncNav('composition');
  setWorkspace('Composition', 'Inspect a proposed collective arrangement');
  clear(workspaceBody);

  const card = el('section', 'card');
  card.append(
    el('div', 'eyebrow', 'FOUNDER NODE → HOUSE / UNTRUSTED CARRIER'),
    el('h2', '', 'Local composition inspection'),
    el('p', 'muted', 'Paste a Workbench inspection descriptor copied from Founder Node. HOUSE validates its declared boundaries and looks for checkout-name candidates under your configured roots. No project is launched, admitted or changed.'),
    el('p', 'muted tiny', 'Pasted JSON and its claimed registry witnesses are not authenticated. A matching checkout name does not establish repository identity, readiness or compatibility.')
  );
  const form = el('form', 'creator-form');
  const input = el('textarea');
  input.rows = 11;
  input.maxLength = 65536;
  input.required = true;
  input.setAttribute('aria-label', 'Paste Founder Node inspection descriptor JSON');
  input.placeholder = '{"schema":"static-collective.founder-node.workbench-inspection.v0.1", ...}';
  const submit = el('button', 'action-button', 'Inspect local candidates');
  submit.type = 'submit';
  const result = el('section', 'card');
  result.setAttribute('aria-live', 'polite');
  result.appendChild(el('p', 'muted', 'Nothing submitted or retained.'));
  form.append(input, submit);
  card.appendChild(form);
  workspaceBody.append(card, result);

  form.addEventListener('submit', async event => {
    event.preventDefault();
    submit.disabled = true;
    clear(result);
    result.appendChild(el('p', 'muted', 'Inspecting configured local roots…'));
    try {
      const body = await api('/api/house/composition/inspect', {
        method: 'POST',
        headers: { 'x-workbench-session': state.bootstrap.session_token },
        body: JSON.stringify({ raw_json: input.value })
      });
      clear(result);
      result.append(
        el('h2', '', 'Inspection-only result'),
        el('p', 'muted', 'Source authenticated: no · execution authorized: no · project admission: not requested.')
      );
      for (const item of body.participants) {
        const row = el('article', 'card');
        row.append(
          el('h3', '', item.project_id_claimed),
          el('p', 'muted', item.repository_claimed),
          el('p', 'muted', 'Local checkout: ' + item.local_state +
            ' · Project identity verified: no · Readiness: unknown · Compatibility: unverified')
        );
        for (const checkout of item.checkouts) {
          const matched = state.repos.find(repo =>
            repo.root_id === checkout.root_id && repo.relative_path === checkout.relative_path);
          row.append(el('p', 'muted tiny', checkout.root_id + ':' + checkout.relative_path +
            ' · HEAD ' + (checkout.head || 'unborn') +
            ' · ' + (checkout.dirty ? 'dirty' : 'clean') +
            ' · ' + (checkout.branch || 'detached')));
          if (matched) {
            const open = el('button', 'quiet-button', 'Inspect checkout details');
            open.type = 'button';
            open.addEventListener('click', () => renderRepoDetail(matched));
            row.appendChild(open);
          }
        }
        result.appendChild(row);
      }
      for (const claim of body.non_claims) {
        result.appendChild(el('p', 'muted tiny', claim));
      }
    } catch (error) {
      clear(result);
      result.appendChild(el('div', 'notice error', error.message || String(error)));
    } finally {
      submit.disabled = false;
    }
  });
}
