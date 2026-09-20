/* HOUSE-FLYWHEEL-002: read-only display for manually imported, self-reported returns.
 * All source-provided content is rendered as text, never HTML or executable URLs.
 * No import, permission, checkout, successor proposal, or project effect is exposed.
 */
async function renderReturnShelf() {
  state.view = 'returns';
  syncNav('returns');
  setWorkspace('Return Shelf', 'What each flight left behind');
  clear(workspaceBody);
  workspaceBody.appendChild(el('div', 'empty-state', 'Reading local return records…'));
  let response;
  try {
    response = await api('/api/house/returns?limit=50');
  } catch (error) {
    if (state.view === 'returns') showError(error);
    return;
  }
  if (state.view !== 'returns') return;
  clear(workspaceBody);

  const intro = el('section', 'card return-shelf-intro');
  intro.append(
    el('div', 'eyebrow', 'LOCAL / READ ONLY / SELF-REPORTED'),
    el('h2', '', 'Capability Return Shelf'),
    el('p', 'muted', 'These are manually supplied Workbench-local reports. No source owner, effect, evidence reference, or reuse claim has been independently verified. A parent reference does not authorize a descendant flight.')
  );
  workspaceBody.appendChild(intro);

  const records = response.records;
  if (!Array.isArray(records) || records.length === 0) {
    workspaceBody.appendChild(el('div', 'empty-state', 'No capability returns recorded locally. This view does not import projects or synthesize returns from operational events.'));
    return;
  }
  const list = el('section', 'return-list');
  list.appendChild(el('div', 'section-heading', 'RECORDED RETURNS — NEWEST FIRST'));
  for (const record of records) {
    const packet = record.packet;
    const card = el('article', 'card return-card');
    const heading = el('h2', '', packet.return_id);
    card.append(
      el('div', 'eyebrow', 'REPORTED · NOT INDEPENDENTLY VERIFIED'),
      heading,
      el('div', 'muted tiny', 'Local receipt #' + record.id + ' · ' + record.received_at),
      el('div', 'repo-meta', 'Flight: ' + packet.flight_ref),
      el('div', 'repo-meta', 'Source owner: ' + packet.source_owner + ' · Ref: ' + packet.source_ref),
      el('div', 'repo-meta', 'Claimed effect: ' + packet.effect_state),
      el('p', '', packet.capability_delta)
    );
    const toggle = el('button', 'quiet-button', 'Inspect reported return');
    toggle.type = 'button';
    toggle.setAttribute('aria-expanded', 'false');
    const details = el('section', 'return-details');
    details.hidden = true;
    function field(label, value) {
      const wrap = el('div', 'return-field');
      wrap.append(el('div', 'eyebrow', label), el('div', 'return-text', value));
      details.appendChild(wrap);
    }
    field('Parent effect · informational, not authorization', packet.parent_effect_ref ?? 'none declared');
    field('Resource costs', packet.resource_costs);
    field('Local digest · deduplication only', record.local_digest);
    field('Evidence references · unverified', packet.evidence_refs.join('\n') || 'none supplied');
    field('Explicit nonclaims', packet.nonclaims.join('\n'));
    field('Possible next steps · inert proposals', packet.proposed_next.join('\n') || 'none proposed');
    const artifacts = el('div', 'return-artifacts');
    artifacts.appendChild(el('div', 'eyebrow', 'ARTIFACTS · REPORTED CAPABILITIES'));
    if (!packet.artifacts.length) artifacts.appendChild(el('div', 'muted', 'No artifacts declared.'));
    for (const artifact of packet.artifacts) {
      const item = el('div', 'return-artifact');
      item.append(
        el('div', 'repo-name', artifact.owner + ' / ' + artifact.artifact_ref),
        el('div', 'muted tiny', artifact.kind + ' · ' + artifact.capability_state + ' (source claim only)'),
        el('div', 'muted tiny', 'Evidence refs: ' + (artifact.evidence_refs.join('; ') || 'none supplied'))
      );
      artifacts.appendChild(item);
    }
    details.appendChild(artifacts);
    toggle.addEventListener('click', () => {
      details.hidden = !details.hidden;
      toggle.setAttribute('aria-expanded', String(!details.hidden));
      toggle.textContent = details.hidden ? 'Inspect reported return' : 'Close reported return';
    });
    card.append(toggle, details);
    list.appendChild(card);
  }
  workspaceBody.appendChild(list);
}
