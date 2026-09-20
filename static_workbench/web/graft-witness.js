/* Experimental GRAFT structural witness. Human graph only; no inferred edges. */
function graftRenderForRide(ride, host) {
  const panel = el('section', 'card native-graft-witness');
  panel.append(el('div', 'eyebrow', 'GRAFT × DOGRAM / STRUCTURAL WITNESS 001'),
    el('h2', '', 'Measure one explicitly declared possibility'),
    el('p', 'muted', 'This is a human-supplied graph of a proposed relationship, NOT a graph extracted from this ride. The ride remains unchanged. Select exactly one edge to add or remove. Dogram reports only structural paths.'));
  const form = el('form', 'native-spin-form');
  const graph = el('textarea'); graph.rows = 5; graph.required = true;
  graph.setAttribute('aria-label', 'Human-declared graph as JSON');
  graph.value = JSON.stringify({
    nodes: ['seed', 'candidate', 'saved_proposal'],
    edges: [['seed', 'candidate']],
  }, null, 2);
  const mode = el('select'); mode.setAttribute('aria-label', 'Public Dogram structural operator');
  for (const [value, label] of [['reach', 'reach@1 · add/remove one edge'],
                                ['ablate', 'ablate@1 · remove one existing edge']]) {
    const option = el('option', '', label); option.value = value; mode.appendChild(option);
  }
  const change = el('textarea'); change.rows = 2; change.required = true;
  change.setAttribute('aria-label', 'One explicitly declared change as JSON');
  change.value = JSON.stringify({op: 'ADD_EDGE', source: 'candidate', target: 'saved_proposal'});
  const queries = el('textarea'); queries.rows = 2; queries.required = true;
  queries.setAttribute('aria-label', 'Declared path queries as JSON');
  queries.value = JSON.stringify([['seed', 'saved_proposal']]);
  mode.addEventListener('change', () => {
    change.value = mode.value === 'reach'
      ? JSON.stringify({op: 'ADD_EDGE', source: 'candidate', target: 'saved_proposal'})
      : JSON.stringify({kind: 'edge', source: 'seed', target: 'candidate'});
  });
  const previewButton = el('button', 'action-button', 'Preview declared GRAFT graph');
  previewButton.type = 'submit';
  const output = el('div', 'native-fuel-preview');
  const label = (title, control) => {
    const field = el('label', 'native-fuel-form');
    field.appendChild(el('span', 'eyebrow', title));
    field.appendChild(control); return field;
  };
  form.append(label('HUMAN GRAPH · JSON', graph), label('DOGRAM OPERATOR', mode),
    label('ONE CHANGE · JSON', change), label('EXPLICIT PATH QUERIES · JSON', queries),
    el('p', 'muted tiny',
      'The prefilled graph is an illustrative fixture. Replace it with your actual declared structure before interpreting any result. No model or source parser invented these nodes or edges.'),
    previewButton, output);
  panel.appendChild(form);
  const history = el('div', 'native-fuel-preview');
  panel.append(el('div', 'eyebrow', 'EARLIER MEASUREMENTS FOR THIS RIDE'), history);
  host.appendChild(panel);

  function showReceipt(record, destination) {
    clear(destination);
    destination.append(el('div', 'repo-name', 'HOUSE witness SHA-256: ' + record.witness_sha256),
      el('p', 'muted tiny', 'Dogram commit: ' + record.witness.dogram_commit),
      el('p', 'muted tiny', record.witness.non_claims.join(' · ')));
    const receipt = record.witness.dogram_receipt;
    destination.append(el('div', 'repo-name', 'DOGRAM ' + receipt.operator + '@'
      + receipt.operator_version + ' · ' + receipt.status),
      el('pre', 'raw-carrier', JSON.stringify(receipt, null, 2)));
  }
  async function refreshHistory() {
    clear(history);
    try {
      const data = await api('/api/house-maxhinal/graft/rides/' + ride.id + '/witnesses');
      if (!data.witnesses.length) {
        history.appendChild(el('p', 'muted tiny', 'No graph measurements saved for this ride.'));
      }
      for (const item of data.witnesses) {
        const open = el('button', 'quiet-button', 'Open witness ' + item.witness_sha256.slice(0, 16));
        open.type = 'button';
        const detail = el('div', 'native-fuel-preview');
        open.addEventListener('click', async () => {
          try { showReceipt(await api('/api/house-maxhinal/graft/witnesses/' + item.witness_sha256), detail); }
          catch (error) { detail.textContent = error.message || String(error); }
        });
        history.append(open, detail);
      }
    } catch (error) { history.textContent = error.message || String(error); }
  }
  form.addEventListener('submit', async event => {
    event.preventDefault(); clear(output); previewButton.disabled = true;
    let request;
    try {
      request = {
        ride_id: ride.id, ride_sha256: ride.ride_sha256,
        graph: JSON.parse(graph.value), operator: mode.value,
        change: JSON.parse(change.value), queries: JSON.parse(queries.value),
      };
      const reviewed = await creatorV2Write('/api/house-maxhinal/graft/preview', request);
      output.append(el('div', 'repo-name', 'Review this EXACT declared specimen before measuring'),
        el('p', 'muted tiny', 'Pinned local Dogram: ' + reviewed.dogram_commit),
        el('p', 'muted tiny', 'Specimen SHA-256: ' + reviewed.specimen_sha256),
        el('pre', 'raw-carrier', JSON.stringify(reviewed.specimen, null, 2)));
      const measure = el('button', 'action-button', 'Run reviewed graph through Dogram');
      measure.type = 'button';
      const outcome = el('div', 'native-fuel-preview');
      measure.addEventListener('click', async () => {
        measure.disabled = true; outcome.textContent = 'Calculating reviewed structure…';
        try {
          // Re-read inputs from the form; server independently checks all frozen digests.
          const now = {
            ride_id: ride.id, ride_sha256: ride.ride_sha256,
            graph: JSON.parse(graph.value), operator: mode.value,
            change: JSON.parse(change.value), queries: JSON.parse(queries.value),
          };
          const result = await creatorV2Write('/api/house-maxhinal/graft/measure', {
            ...now, expected_specimen_sha256: reviewed.specimen_sha256,
            expected_dogram_commit: reviewed.dogram_commit,
          });
          showReceipt(result, outcome);
          await Promise.all([refreshHistory(), loadEvents()]);
        } catch (error) {
          outcome.textContent = (error.message || String(error)) + ' · Review the graph again if anything changed.';
        } finally { measure.disabled = false; }
      });
      output.append(measure, outcome);
    } catch (error) {
      output.appendChild(el('div', 'notice error', error.message || String(error)));
    } finally { previewButton.disabled = false; }
  });
  refreshHistory();
}
