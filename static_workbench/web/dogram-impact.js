/* HOUSE Impact Desk 001. Only explicit local, human-reviewed calculations. */
function renderDogramImpactDesk() {
  state.view = 'dogram-impact'; syncNav('dogram-impact');
  setWorkspace('Dogram Lab', 'Committed-source impact');
  clear(workspaceBody);

  const header = el('article', 'card');
  header.append(
    el('div', 'eyebrow', 'EXPERIMENTAL / LOCAL / READ-ONLY'),
    el('h2', '', 'Measure a Python dependency change'),
    el('p', 'muted',
      'Select a discovered Python repository. Preview its latest commit against its first parent, then deliberately run the pinned local Dogram research kernel. Uncommitted changes are not measured.')
  );
  const laws = el('div', 'law-strip');
  [
    'structural reachability != causation',
    'calculation != quality verdict',
    'HOUSE report != public Dogram receipt',
  ].forEach(text => laws.appendChild(el('span', 'law-chip', text)));
  header.appendChild(laws);
  workspaceBody.appendChild(header);

  const card = el('section', 'card creator-search');
  const form = el('form', 'creator-form');
  const picker = el('select');
  picker.setAttribute('aria-label', 'Python repository to compare');
  for (const repo of state.repos.filter(item => (item.stacks || []).includes('python'))) {
    const option = el('option', '', item.root_id + ':' + item.relative_path);
    option.value = JSON.stringify({ root_id: repo.root_id, repo_path: repo.relative_path });
    picker.appendChild(option);
  }
  const previewButton = el('button', 'action-button', 'Preview committed source');
  previewButton.type = 'submit'; previewButton.disabled = !picker.options.length;
  form.append(picker, previewButton);
  const previewHost = el('div', 'native-fuel-preview');
  card.append(
    el('h2', '', 'Source and version gate'),
    el('p', 'muted tiny', 'This instrument never imports or executes the selected project. It only reads bounded Python blobs from two Git commits.'),
    form, previewHost
  );
  workspaceBody.appendChild(card);

  const saved = el('section', 'card creator-search');
  const savedForm = el('form', 'creator-form');
  const savedId = el('input');
  savedId.placeholder = 'Saved report SHA-256';
  savedId.maxLength = 64;
  savedId.setAttribute('aria-label', 'Saved Dogram impact report ID');
  const load = el('button', 'quiet-button', 'Open saved report');
  load.type = 'submit';
  const savedHost = el('div', 'native-fuel-preview');
  savedForm.append(savedId, load);
  saved.append(el('h2', '', 'Return to an earlier measurement'), savedForm, savedHost);
  workspaceBody.appendChild(saved);

  function showReport(data, host) {
    clear(host);
    const report = data.report;
    const result = report.dogram_internal_result;
    const d = el('dl', 'definition-grid');
    const metrics = [
      ['HOUSE report', data.report_id],
      ['Dogram commit', report.dogram_commit],
      ['Baseline', report.source.baseline_commit],
      ['Candidate', report.source.candidate_commit],
      ['Nodes added / removed', result.node_delta.added.length + ' / ' + result.node_delta.removed.length],
      ['Edges added / removed', result.edge_delta.added.length + ' / ' + result.edge_delta.removed.length],
      ['Reachability gained / lost', result.reachability_delta.gained.length + ' / ' + result.reachability_delta.lost.length],
    ];
    metrics.forEach(([label, value]) => d.append(el('dt', '', label), el('dd', '', String(value))));
    host.append(el('h2', '', 'Measured structural delta'), d,
      el('div', 'muted tiny', report.non_claims.join(' · ')));
    const pre = el('pre', 'raw-carrier', JSON.stringify(report, null, 2));
    pre.style.maxHeight = '340px'; pre.style.overflow = 'auto';
    host.appendChild(pre);
    savedId.value = data.report_id;
  }

  function showPreview(info) {
    clear(previewHost);
    const d = el('dl', 'definition-grid');
    [
      ['Repository', info.root_id + ':' + info.repo_path],
      ['Baseline', info.baseline_commit],
      ['Candidate', info.candidate_commit],
      ['Python sources', info.baseline_file_count + ' → ' + info.candidate_file_count],
      ['Working tree', info.working_tree_dirty ? 'DIRTY; ignored for this comparison' : 'Excluded even if clean'],
      ['Dogram checkout', !info.dogram.available ? 'Not discovered' : info.dogram.clean ? 'Clean' : 'DIRTY; execution refused'],
      ['Pinned Dogram HEAD', info.dogram.commit || 'Unavailable'],
      ['Frozen input address', info.input_sha256],
    ].forEach(([label, value]) => d.append(el('dt', '', label), el('dd', '', value)));
    const run = el('button', 'action-button', 'Run exactly this Dogram comparison');
    run.type = 'button';
    run.disabled = !info.dogram.available || !info.dogram.clean;
    const feedback = el('div', 'native-fuel-preview');
    run.addEventListener('click', async () => {
      run.disabled = true; feedback.textContent = 'Measuring the confirmed committed snapshots…';
      try {
        const data = await api('/api/dogram/impact/run', {
          method: 'POST',
          headers: { 'x-workbench-session': state.bootstrap.session_token },
          body: JSON.stringify({
            root_id: info.root_id, repo_path: info.repo_path,
            expected_input_sha256: info.input_sha256,
            expected_candidate_commit: info.candidate_commit,
            expected_dogram_commit: info.dogram.commit,
          }),
        });
        showReport(data, feedback);
        await loadEvents();
      } catch (error) {
        feedback.textContent = error.message || String(error);
      } finally {
        run.disabled = false;
      }
    });
    previewHost.append(d, run, feedback);
    if (!info.dogram.available || !info.dogram.clean) {
      feedback.appendChild(el('div', 'notice error', 'Install a clean Dogram checkout under the configured roots before running this experiment.'));
    }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    previewButton.disabled = true;
    previewHost.textContent = 'Inspecting the selected committed source…';
    try {
      const selected = JSON.parse(picker.value);
      const info = await api('/api/dogram/impact/preview', {
        method: 'POST',
        headers: { 'x-workbench-session': state.bootstrap.session_token },
        body: JSON.stringify(selected),
      });
      showPreview(info);
    } catch (error) {
      previewHost.textContent = error.message || String(error);
    } finally {
      previewButton.disabled = false;
    }
  });
  savedForm.addEventListener('submit', async event => {
    event.preventDefault();
    savedHost.textContent = 'Reading saved report…';
    try {
      showReport(await api('/api/dogram/impact/reports/' + encodeURIComponent(savedId.value)), savedHost);
    } catch (error) {
      savedHost.textContent = error.message || String(error);
    }
  });
}
