/* GRAFT v0.1: human-declared FORK-inspired proposals, never automatic action. */
const graftRoundState = {selectedByRide: Object.create(null)};

function graftRoundRenderForRide(ride, host) {
  const panel = el('section', 'card native-graft-rounds');
  panel.append(
    el('div', 'eyebrow', 'GRAFT / THREE RECOVERABLE PROPOSALS'),
    el('h2', '', 'Declare KEEP · BEND · INTRUDER'),
    el('p', 'muted', 'These are three deterministic transformation QUESTIONS, not generated finished ideas. You declare the preserved thread, flexible element, and unrelated intruder. No source meaning or lineage is inferred. Saving a round does not select a candidate.')
  );
  const form = el('form', 'native-spin-form');
  const makeText = (name, example) => {
    const field = el('label', 'native-fuel-form');
    field.appendChild(el('span', 'eyebrow', name));
    const input = el('textarea');
    input.rows = 2; input.required = true; input.maxLength = 400;
    input.placeholder = example; input.setAttribute('aria-label', name);
    field.appendChild(input);
    return [field, input];
  };
  const [keepField, keep] = makeText('KEEP / preserved thread', 'What specific property should survive?');
  const [bendField, bend] = makeText('BEND / flexible element', 'What implementation, context, or mechanism may change?');
  const [intruderField, intruder] = makeText('INTRUDER / explicitly selected foreign mechanism',
    'What unrelated but reviewable mechanism or selected source should enter?');
  const moveField = el('label', 'native-fuel-form');
  moveField.appendChild(el('span', 'eyebrow', 'TRANSFORMATION'));
  const move = el('select'); move.setAttribute('aria-label', 'GRAFT transformation move');
  for (const name of ['fuse', 'invert', 'continue', 'wildcard']) {
    const option = el('option', '', name); option.value = name; move.appendChild(option);
  }
  moveField.appendChild(move);
  const laneField = el('label', 'native-fuel-form');
  laneField.appendChild(el('span', 'eyebrow', 'WHY BRING THE INTRUDER HERE? (HUMAN CLAIM)'));
  const lane = el('select'); lane.setAttribute('aria-label', 'Declared relation lane');
  for (const [value, label] of [
    ['semantic', 'Resemblance (hypothesis, not evidence)'],
    ['lineage', 'Lineage (human-declared; not verified here)'],
    ['active_tension', 'Shared unresolved tension'],
    ['human_link', 'Explicit human link'],
    ['rejected_parallel', 'Previously rejected alternative'],
  ]) {
    const option = el('option', '', label); option.value = value; lane.appendChild(option);
  }
  laneField.appendChild(lane);
  const [questionField, question] = makeText('OPTIONAL HUMAN QUESTION', 'What do you want to investigate?');
  question.required = false;
  const previewButton = el('button', 'action-button', 'Preview three GRAFT candidate questions');
  previewButton.type = 'submit';
  const result = el('div', 'native-fuel-preview');
  form.append(keepField, bendField, intruderField, moveField, laneField, questionField,
    previewButton, result);
  panel.appendChild(form);
  const chosen = el('div', 'notice',
    'No candidate selected for Dogram. Existing ride-only graph measurements remain available.');
  panel.appendChild(chosen);
  const history = el('div', 'native-fuel-preview');
  panel.append(el('div', 'eyebrow', 'SAVED PROPOSAL ROUNDS'), history);
  host.appendChild(panel);

  function refreshSelection() {
    const id = graftRoundState.selectedByRide[String(ride.id)] || null;
    chosen.textContent = id
      ? 'Selected for next Dogram preview: ' + id + '. No change or source relationship is automatically inferred.'
      : 'No candidate selected for Dogram. You can still measure a ride-only declared graph.';
  }
  function showRound(saved, target) {
    clear(target);
    const round = saved.round;
    target.append(
      el('div', 'repo-name', 'Round SHA-256: ' + saved.round_sha256),
      el('p', 'muted tiny', 'Parent ride #' + round.ride_id + ' · ' + round.ride_sha256),
      el('pre', 'raw-carrier', JSON.stringify(round.declarations, null, 2)),
      el('p', 'muted tiny', round.non_claims.join(' · '))
    );
    for (const candidate of round.candidates) {
      const card = el('article', 'creator-preview-source');
      card.append(
        el('div', 'repo-name', candidate.title + ' / ' + candidate.variant),
        el('pre', 'raw-carrier', candidate.transformation_question),
        el('p', 'muted tiny', 'Possible next experiment: ' + candidate.next_act_question),
        el('p', 'muted tiny', 'Pressure: ' + candidate.pressure_question),
        el('p', 'muted tiny', 'Candidate SHA-256: ' + candidate.candidate_sha256)
      );
      const choose = el('button', 'quiet-button', 'Select this proposal for Dogram');
      choose.type = 'button';
      choose.addEventListener('click', () => {
        graftRoundState.selectedByRide[String(ride.id)] = candidate.candidate_sha256;
        refreshSelection();
        target.appendChild(el('div', 'notice',
          'Candidate selected for subsequent graph preview. The graph itself must still be declared and reviewed separately.'));
      });
      card.appendChild(choose);
      target.appendChild(card);
    }
    refreshSelection();
  }

  async function loadHistory() {
    clear(history);
    try {
      const listed = await api('/api/house-maxhinal/graft/rides/' + ride.id + '/rounds');
      if (!listed.rounds.length) history.appendChild(el('p', 'muted tiny', 'No saved GRAFT rounds for this ride.'));
      for (const item of listed.rounds) {
        const open = el('button', 'quiet-button', 'Open round ' + item.round_sha256.slice(0, 16));
        open.type = 'button';
        const details = el('div', 'native-fuel-preview');
        open.addEventListener('click', async () => {
          try { showRound(await api('/api/house-maxhinal/graft/rounds/' + item.round_sha256), details); }
          catch (error) { details.textContent = error.message || String(error); }
        });
        history.append(open, details);
      }
    } catch (error) { history.textContent = error.message || String(error); }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault(); clear(result); previewButton.disabled = true;
    try {
      const request = {
        ride_id: ride.id, ride_sha256: ride.ride_sha256,
        keep: keep.value, bend: bend.value, intruder: intruder.value,
        move: move.value, relation_lane: lane.value, question: question.value,
      };
      const reviewed = await creatorV2Write('/api/house-maxhinal/graft/rounds/preview', request);
      result.append(
        el('div', 'repo-name', 'Review all three candidates and human declarations before saving'),
        el('p', 'muted tiny', 'Round SHA-256: ' + reviewed.round_sha256),
        el('pre', 'raw-carrier', JSON.stringify(reviewed.round, null, 2))
      );
      const save = el('button', 'action-button', 'Save this reviewed GRAFT round');
      save.type = 'button';
      const savedOutput = el('div', 'native-fuel-preview');
      save.addEventListener('click', async () => {
        save.disabled = true;
        try {
          const current = {
            ride_id: ride.id, ride_sha256: ride.ride_sha256,
            keep: keep.value, bend: bend.value, intruder: intruder.value,
            move: move.value, relation_lane: lane.value, question: question.value,
          };
          const saved = await creatorV2Write('/api/house-maxhinal/graft/rounds', {
            ...current, expected_round_sha256: reviewed.round_sha256,
          });
          showRound(saved, savedOutput);
          await Promise.all([loadHistory(), loadEvents()]);
        } catch (error) {
          savedOutput.textContent = (error.message || String(error)) + ' · Review the proposal again if its declarations changed.';
        } finally { save.disabled = false; }
      });
      result.append(save, savedOutput);
    } catch (error) {
      result.appendChild(el('div', 'notice error', error.message || String(error)));
    } finally { previewButton.disabled = false; }
  });
  refreshSelection();
  loadHistory();
}
