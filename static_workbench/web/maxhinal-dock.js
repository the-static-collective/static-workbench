/* Maxhinal Ride Dock: humans move actual .maxhinal.json receipts into HOUSE.
 * HOUSE never runs or replaces the Daily Slice machine.
 */
function maxhinalSourceDoor() {
  const repo = state.repos.find(item => item.name.toLowerCase() === 'the-daily-slice');
  const card = el('article', 'card');
  card.append(el('div', 'eyebrow', 'SOURCE-OWNED MACHINE / SAME ENGINE, DIFFERENT HANDS'),
    el('h2', '', 'Hugh Jackman Discontinuity Maxhinal'),
    el('p', 'muted', 'Run the actual Daily Slice machine in its own local browser or CLI. Export its .maxhinal.json ride, then review and dock that ride here. Ordinary Creator Desk source lines are not automatically converted into Slice gas.'));
  if (repo) {
    const path = repo.path + '/artifacts/2026-08-25/hugh-jackman-discontinuity-machine.html';
    card.appendChild(el('div', 'muted tiny', 'Expected local HTML entry (check your checkout before opening):'));
    const pre = el('pre', 'raw-carrier', path);
    const copy = el('button', 'quiet-button', 'Copy expected local Maxhinal file path');
    copy.type = 'button';
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(path);
        copy.textContent = 'Path copied — open with your local file manager.';
      } catch (_) { copy.textContent = 'Copy the path shown above manually.'; }
    });
    card.append(pre, copy);
  } else {
    card.appendChild(el('p', 'muted', 'Daily Slice is not discovered under HOUSE roots. Install or select its checkout to run the original machine; the Ride Dock can still accept a human-supplied ride.'));
  }
  const guide = el('a', 'quiet-button', 'Read the source-owned Maxhinal documentation');
  guide.href = 'https://github.com/the-static-collective/the-daily-slice/blob/main/artifacts/maxhinal/README.md';
  guide.target = '_blank'; guide.rel = 'noopener noreferrer';
  card.appendChild(guide);
  return card;
}
function maxhinalRenderDock(host, s) {
  host.appendChild(maxhinalSourceDoor());
  if (!s.pack) return;
  const card = el('article', 'card maxhinal-ride-dock');
  card.append(el('div', 'eyebrow', 'MAXHINAL / EXPLICIT RIDE RE-ENTRY'),
    el('h2', '', 'Dock a real ride with this source pack'),
    el('p', 'muted', 'This creates an explicit creative-use association between two distinct sources; the ride gas remains Daily Slice, and its reported replay state is not independently verified by HOUSE. Save an in-progress draft before reloading.'));
  const available = (s.maxhinalRides || []).filter(item => item.pack_id === s.pack.id);
  const chooser = el('select');
  chooser.setAttribute('aria-label', 'Choose a docked Maxhinal ride for next draft revision');
  const blank = el('option', '', 'No ride linked');
  blank.value = '';
  chooser.appendChild(blank);
  for (const item of available) {
    const option = el('option', '', 'Ride #' + item.id + ' · ' + item.ride_id + ' · ' + item.ride_sha256.slice(0, 12));
    option.value = String(item.id);
    chooser.appendChild(option);
  }
  const linked = s.linkedRideId === undefined ? (s.draft?.maxhinal_ride_id || null) : s.linkedRideId;
  chooser.value = linked === null ? '' : String(linked);
  chooser.addEventListener('change', () => {
    s.linkedRideId = chooser.value ? Number(chooser.value) : null;
  });
  card.appendChild(el('div', 'muted tiny', 'Attach a reviewed docked ride on your NEXT explicit draft save:'));
  card.appendChild(chooser);
  const file = el('textarea', 'maxhinal-ride-json');
  file.rows = 5; file.maxLength = 131072;
  file.setAttribute('aria-label', 'Paste actual exported Maxhinal ride JSON');
  file.placeholder = 'Paste a complete exported .maxhinal.json ride here. No model call or execution happens.';
  const preview = el('button', 'action-button', 'Preview this Maxhinal ride');
  preview.type = 'button';
  const feedback = el('div', 'maxhinal-ride-preview');
  card.append(file, preview, feedback);
  preview.addEventListener('click', async () => {
    clear(feedback);
    const raw_json = file.value;
    try {
      const packet = await creatorV2Write('/api/creator/maxhinal/preview', {
        pack_id: s.pack.id, raw_json,
      });
      const checksum = packet.ride_sha256;
      feedback.append(
        el('div', 'repo-name', packet.ride_id + ' · ' + checksum),
        el('div', 'muted tiny', 'Corpus (self-reported): ' + packet.corpus_digest + ' · Replay (self-reported): ' + packet.reported_replay),
        el('div', 'muted tiny', packet.source_slice_ids.length + ' Slice gas refs · ' + packet.operations.length + ' operations · ' + packet.output_count + ' derived outputs')
      );
      packet.operations.forEach(op => feedback.appendChild(el('div', 'muted tiny', op.id + ' / ' + op.mode + ' → ' + op.outputs.join(', '))));
      const residuals = el('div', 'gap-list');
      packet.residuals.forEach(res => residuals.appendChild(el('div', 'gap-item', 'RESIDUAL ' + res.id + ' / ' + res.code + ': ' + res.message)));
      packet.bad_spins.forEach(bad => residuals.appendChild(el('div', 'gap-item', 'BAD SPIN ' + bad.id + ': ' + bad.reason)));
      feedback.appendChild(residuals);
      feedback.appendChild(el('p', 'muted tiny', 'Review all material in the original Maxhinal before saving. HOUSE stores the entire untrusted JSON byte-for-byte, and does not recompute its operations or claim a matching local corpus.'));
      const save = el('button', 'action-button', 'Dock this reviewed ride locally');
      save.type = 'button';
      save.addEventListener('click', async () => {
        save.disabled = true;
        try {
          const saved = await creatorV2Write('/api/creator/maxhinal/rides', {
            pack_id: s.pack.id, raw_json, expected_ride_sha256: checksum,
          });
          s.maxhinalRides.unshift(saved);
          s.linkedRideId = saved.id;
          const option = el('option', '', 'Ride #' + saved.id + ' · ' + saved.ride_id + ' · ' + saved.ride_sha256.slice(0, 12));
          option.value = String(saved.id);
          chooser.appendChild(option); chooser.value = String(saved.id);
          file.value = '';
          creatorV2Message(feedback, 'Saved local ride snapshot #' + saved.id + '. Save a draft revision to record this explicit creative-use association.', false);
          save.remove();
        } catch (error) {
          creatorV2Message(feedback, error.message || String(error), true);
          save.disabled = false;
        }
      });
      feedback.appendChild(save);
    } catch (error) {
      creatorV2Message(feedback, error.message || String(error), true);
    }
  });
  host.appendChild(card);
}
