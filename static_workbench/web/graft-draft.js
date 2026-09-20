/* GRAFT 003: explicit working-draft edits on immutable candidate IDs. */
async function graftDraftOpen(candidateSha, host) {
  clear(host);
  host.appendChild(el('p', 'muted tiny', 'Opening source-bound local draft…'));

  const base = '/api/house-maxhinal/graft/candidates/' + candidateSha + '/draft';
  async function render(record) {
    clear(host);
    const draft = record.draft;
    host.append(
      el('div', 'eyebrow', 'GRAFT / WORKING DRAFT / PROPOSED, NOT RUN'),
      el('p', 'muted tiny', 'Candidate SHA-256: ' + candidateSha),
      el('p', 'muted tiny', 'Source ride #' + draft.ride_id + ' · round ' + draft.round_sha256),
      el('p', 'muted tiny', 'Revision ' + record.revision + (record.draft_sha256
        ? ' · SHA-256 ' + record.draft_sha256 : ' · initial editable template (not saved)')),
      el('div', 'notice', 'The mechanism and experiment below are a human-editable proposal. Nothing here runs code, records an observation, changes a project or publishes a request.')
    );
    const form = el('form', 'native-spin-form');
    const field = (label, value, rows, maxLength) => {
      const wrap = el('label', 'native-fuel-form');
      wrap.appendChild(el('span', 'eyebrow', label));
      const input = rows === 1 ? el('input') : el('textarea');
      if (rows > 1) input.rows = rows;
      input.value = value || '';
      input.maxLength = maxLength; input.required = true;
      input.setAttribute('aria-label', label);
      wrap.appendChild(input); form.appendChild(wrap);
      return input;
    };
    host.appendChild(el('div', 'muted tiny', 'Source references: ' + JSON.stringify(draft.source_refs)));
    const title = field('WORKING TITLE', draft.title, 1, 160);
    const body = field('EDITABLE MECHANISM / CONTENT DRAFT', draft.body, 9, 8192);
    const fixture = field('EXPERIMENT / DECLARED INPUT', draft.experiment.input, 3, 1200);
    const procedure = field('EXPERIMENT / BOUNDED PROCEDURE', draft.experiment.procedure, 3, 1200);
    const observable = field('EXPERIMENT / PREDECLARED OBSERVABLE', draft.experiment.observable, 3, 1200);
    const stop = field('EXPERIMENT / STOP CONDITION', draft.experiment.stop_condition, 3, 1200);
    const assumptions = field('UNVERIFIED ASSUMPTIONS', draft.assumptions, 3, 2000);
    const unresolved = field('REMAINING QUESTIONS / COUNTEREXAMPLE', draft.unresolved, 3, 2000);
    const save = el('button', 'action-button', 'Save explicit local draft revision');
    save.type = 'submit';
    const status = el('div', 'creator-feedback');
    form.append(save, status);
    host.appendChild(form);
    const history = el('div', 'native-fuel-preview');
    host.append(el('div', 'eyebrow', 'EARLIER EDITABLE DRAFT REVISIONS'), history);

    async function loadHistory() {
      clear(history);
      const result = await api(base + '/revisions');
      if (!result.revisions.length) {
        history.appendChild(el('p', 'muted tiny', 'No saved revisions yet.'));
      }
      for (const previous of result.revisions) {
        const open = el('button', 'quiet-button',
          'Inspect revision ' + previous.revision + ' · ' + previous.draft_sha256.slice(0, 12));
        open.type = 'button';
        const details = el('div', 'native-fuel-preview');
        open.addEventListener('click', async () => {
          clear(details);
          try {
            const earlier = await api(base + '/revisions/' + previous.revision);
            details.append(
              el('p', 'muted tiny', 'Historical immutable revision · read-only'),
              el('pre', 'raw-carrier', JSON.stringify(earlier.draft, null, 2))
            );
          } catch (error) { details.textContent = error.message || String(error); }
        });
        history.append(open, details);
      }
    }
    form.addEventListener('submit', async event => {
      event.preventDefault(); clear(status); save.disabled = true;
      try {
        const saved = await creatorV2Write('/api/house-maxhinal/graft/drafts', {
          candidate_sha256: candidateSha,
          expected_revision: record.revision,
          expected_draft_sha256: record.draft_sha256,
          title: title.value, body: body.value,
          experiment: {
            input: fixture.value, procedure: procedure.value,
            observable: observable.value, stop_condition: stop.value,
          },
          assumptions: assumptions.value, unresolved: unresolved.value,
        });
        await render(saved);
        await loadEvents();
      } catch (error) {
        status.appendChild(el('div', 'notice error', (error.message || String(error)) +
          ' · If this draft was revised elsewhere, reopen the candidate before editing.'));
        save.disabled = false;
      }
    });
    try { await loadHistory(); }
    catch (error) { history.textContent = error.message || String(error); }
  }

  try { await render(await api(base)); }
  catch (error) {
    clear(host);
    host.appendChild(el('div', 'notice error', error.message || String(error)));
  }
}
