/* GROUNDKEEPER-001: explicit operator-triggered synthetic-only field lab. */
async function groundkeeperView() {
  state.view = 'groundkeeper';
  syncNav('groundkeeper');
  setWorkspace('GROUNDKEEPER / FIELD LAB', 'Compose a synthetic ground');
  clear(workspaceBody);

  const intro = el('article', 'card');
  intro.append(
    el('h2', '', 'GROUNDKEEPER-001 · first ignition'),
    el('p', 'muted', 'One simulated ground channel, coupled sound and visual instruments, and three controlled topology experiments. No microphone, electrical ground, TranchNOSE optical apparatus, project executor, or external service is accessed.'),
    el('div', 'terminal-law', 'A measured difference is not an admission decision.')
  );
  const form = el('form', 'card');
  const label = el('label', '', 'Reproducible synthetic seed');
  const seed = el('input');
  seed.value = 'static-first-ignition';
  seed.maxLength = 128;
  seed.required = true;
  label.appendChild(seed);
  const launch = el('button', 'action-button', 'Run synthetic first flight');
  launch.type = 'submit';
  form.append(label, launch);
  const result = el('section', 'groundkeeper-output');
  result.appendChild(el('div', 'muted', 'No experiment run in this browser session.'));
  workspaceBody.append(intro, form, result);

  form.addEventListener('submit', async event => {
    event.preventDefault();
    launch.disabled = true;
    clear(result);
    result.appendChild(el('div', 'muted', 'Running bounded synthetic experiment…'));
    try {
      const packet = await api('/api/groundkeeper/first-ignition?seed=' + encodeURIComponent(seed.value));
      if (state.view !== 'groundkeeper') return;
      clear(result);
      const summary = el('article', 'card');
      summary.append(
        el('div', 'eyebrow', packet.status),
        el('h2', '', 'First flight receipt'),
        el('div', 'muted tiny', 'Receipt: ' + packet.receipt_digest),
        el('p', '', 'Observed samples: ' + packet.source.sample_count + ' · ' + packet.source.kind),
        el('p', '', 'Baseline mean |sound|: ' + packet.simulation.baseline.mean_abs_sound
          + ' · mean |visual|: ' + packet.simulation.baseline.mean_abs_visual)
      );
      const copy = el('button', 'quiet-button', 'Copy complete experimental receipt');
      copy.type = 'button';
      copy.addEventListener('click', async () => {
        const payload = JSON.stringify(packet, null, 2);
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) throw Error('Clipboard unavailable');
          await navigator.clipboard.writeText(payload);
          copy.textContent = 'Receipt copied';
        } catch (_) {
          const fallback = el('textarea', 'handoff-manual');
          fallback.readOnly = true; fallback.value = payload; fallback.rows = 6;
          summary.appendChild(fallback);
          copy.textContent = 'Select and copy the receipt below';
        }
      });
      summary.appendChild(copy);
      result.appendChild(summary);

      const notes = el('article', 'card');
      notes.append(el('h2', '', 'Derived musical phrase'),
        el('p', 'muted tiny', 'An artistic mapping of simulated amplitudes, not notes detected in the ground.'),
        el('p', '', packet.simulation.baseline.notes.map(n => n.note).join(' · ')));
      result.appendChild(notes);

      const visual = el('article', 'card');
      visual.append(el('h2', '', 'Derived visual frame'),
        el('p', 'muted tiny', 'Synthetic visual transformation at sample tick 0.'));
      const frame = el('div');
      frame.style.display = 'grid';
      frame.style.gridTemplateColumns = 'repeat(8, minmax(0, 24px))';
      frame.style.gap = '3px';
      const pixels = packet.simulation.baseline.frames[0].pixels;
      for (const row of pixels) for (const value of row) {
        const pixel = el('div');
        pixel.style.width = '100%'; pixel.style.aspectRatio = '1';
        pixel.style.borderRadius = '3px';
        pixel.style.backgroundColor = 'hsl(165 65% ' + (15 + 68 * value) + '%)';
        frame.appendChild(pixel);
      }
      visual.appendChild(frame);
      result.appendChild(visual);

      const candidates = el('section', 'house-section');
      candidates.appendChild(el('h2', '', 'Three experimental GRAFT candidates'));
      candidates.appendChild(el('p', 'muted', 'These are simulator graph comparisons only. Copy a graph for human review; GRAFT and Dogram are not automatically invoked.'));
      for (const candidate of packet.simulation.candidates) {
        const card = el('article', 'card');
        card.append(
          el('strong', '', candidate.name.replaceAll('_', ' ')),
          el('div', 'muted tiny', candidate.disposition + ' · ' + candidate.graph_digest),
          el('p', '', 'Mean absolute state delta: ' + candidate.observed_in_simulation.mean_absolute_state_delta),
          el('p', 'muted tiny', 'Sound delta: ' + candidate.observed_in_simulation.sound_energy_delta
            + ' · Visual delta: ' + candidate.observed_in_simulation.visual_energy_delta)
        );
        const graph = el('pre', '', JSON.stringify(candidate.graph, null, 2));
        card.appendChild(graph);
        const copyGraph = el('button', 'quiet-button', 'Copy graph for human review');
        copyGraph.type = 'button';
        copyGraph.addEventListener('click', async () => {
          const payload = JSON.stringify({
            experiment: 'GROUNDKEEPER-001',
            simulation_receipt_digest: packet.receipt_digest,
            candidate_name: candidate.name,
            graph: candidate.graph,
            candidate_graph_digest: candidate.graph_digest,
            status: 'UNREVIEWED_EXPERIMENT',
          }, null, 2);
          try {
            if (!navigator.clipboard || !navigator.clipboard.writeText) throw Error('Clipboard unavailable');
            await navigator.clipboard.writeText(payload);
            copyGraph.textContent = 'Graph copied for review';
          } catch (_) {
            const fallback = el('textarea', 'handoff-manual');
            fallback.readOnly = true; fallback.value = payload; fallback.rows = 5;
            card.appendChild(fallback);
            copyGraph.textContent = 'Select and copy graph below';
          }
        });
        card.appendChild(copyGraph);
        candidates.appendChild(card);
      }
      result.appendChild(candidates);
    } catch (error) {
      clear(result);
      result.appendChild(el('div', 'notice error', error.message || String(error)));
    } finally {
      launch.disabled = false;
    }
  });
}
