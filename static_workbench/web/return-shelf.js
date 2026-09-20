/* HOUSE-FLYWHEEL-003: reported returns plus explicit, inert human-selected preview.
 * All source-provided content is text, never HTML or executable URLs.
 * No import, permission, checkout, autonomous successor, or project effect.
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
  // A human chooses exactly two individual owner-scoped artifacts; there is no
  // automatic pairing, usefulness score, or reuse/equivalence assertion.
  const selected = new Map();
  let previewRevision = 0;
  const loom = el('section', 'card return-loom');
  const count = el('div', 'muted tiny', '0 / 2 exact artifacts selected');
  const question = el('input');
  question.type = 'text';
  question.maxLength = 512;
  question.placeholder = 'What specific relationship would you test?';
  question.setAttribute('aria-label', 'Composition question');
  const previewButton = el('button', 'action-button', 'Preview selected composition');
  previewButton.type = 'button';
  previewButton.disabled = true;
  const previewResult = el('div', 'return-loom-result');
  function syncSelection() {
    count.textContent = selected.size + ' / 2 exact artifacts selected';
    previewButton.disabled = selected.size !== 2 || !question.value.trim();
    clear(previewResult);
    previewRevision += 1;
  }
  question.addEventListener('input', syncSelection);
  previewButton.addEventListener('click', async () => {
    if (selected.size !== 2 || !question.value.trim()) return;
    const revision = ++previewRevision;
    const payload = { selections: [...selected.values()], question: question.value };
    previewButton.disabled = true;
    clear(previewResult);
    previewResult.appendChild(el('div', 'muted', 'Preparing inert preview…'));
    try {
      const proposal = await api('/api/house/loom/preview', {
        method: 'POST',
        headers: { 'X-Workbench-Session': state.bootstrap.session_token },
        body: JSON.stringify(payload),
      });
      if (state.view !== 'returns' || revision !== previewRevision) return;
      clear(previewResult);
      previewResult.append(
        el('div', 'eyebrow', 'INERT / UNRUN / NOT AUTHORIZED'),
        el('div', 'repo-meta', 'Proposal digest (local fingerprint): ' + proposal.proposal_digest),
        el('div', 'muted tiny', 'Compatibility: ' + proposal.compatibility + ' · execution: ' + proposal.execution),
        el('pre', 'code-preview', JSON.stringify(proposal, null, 2))
      );
    } catch (error) {
      if (state.view !== 'returns' || revision !== previewRevision) return;
      clear(previewResult);
      previewResult.appendChild(el('div', 'notice error', error.message || String(error)));
    } finally {
      if (state.view === 'returns' && revision === previewRevision) {
        previewButton.disabled = selected.size !== 2 || !question.value.trim();
      }
    }
  });
  loom.append(
    el('div', 'eyebrow', 'CAPABILITY LOOM / EXPERIMENTAL / NO EFFECTS'),
    el('h2', '', 'Select two artifacts to explore'),
    el('p', 'muted', 'Expand return cards and select exactly two exact references. The preview preserves each original identity and reports compatibility, verification, and authorization as unevaluated. It cannot run a flight.'),
    count, question, previewButton, previewResult
  );
  workspaceBody.appendChild(loom);

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
      const checkbox = el('input');
      checkbox.type = 'checkbox';
      checkbox.setAttribute('aria-label', 'Select artifact ' + artifact.owner + ' / ' + artifact.artifact_ref + ' from ' + packet.return_id);
      const choice = {
        return_id: packet.return_id,
        local_digest: record.local_digest,
        owner: artifact.owner,
        artifact_ref: artifact.artifact_ref,
      };
      const choiceKey = JSON.stringify(choice);
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          const sameIdentitySelected = [...selected.values()].some(
            other => other.owner === choice.owner && other.artifact_ref === choice.artifact_ref
          );
          if (selected.size >= 2 || sameIdentitySelected) {
            checkbox.checked = false;
            return;
          }
          selected.set(choiceKey, choice);
        } else {
          selected.delete(choiceKey);
        }
        syncSelection();
      });
      const choiceLabel = el('label', 'return-artifact-choice');
      choiceLabel.append(checkbox, el('span', '', 'Select this exact reported artifact'));
      item.appendChild(choiceLabel);
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
