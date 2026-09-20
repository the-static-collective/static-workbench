// LAUNCHPAD-001: read-only staged first-flight map, never auto-run commands.
// Uses the shared local HOUSE API and safe textContent rendering helpers.
async function renderLaunchpad() {
  state.view = 'launchpad'; syncNav('launchpad');
  setWorkspace('Launchpad', 'Start the STATIC OS train');
  clear(workspaceBody);
  const data = await api('/api/launchpad');
  if (state.view !== 'launchpad') return;
  const intro = el('section', 'card');
  intro.append(
    el('h2', '', 'HOUSE is awake. The next flights are separately gated.'),
    el('p', 'muted', 'This desk tells you what to do next. It does not run host installers, select disks, build an ISO or mark an unwitnessed boot as successful.'));
  workspaceBody.appendChild(intro);
  for (const gate of data.gates) {
    const card = el('section', 'card');
    card.append(el('div', 'eyebrow', gate.id.toUpperCase() + ' · ' + gate.state.replaceAll('_', ' ')));
    card.append(el('h2', '', gate.title), el('p', 'muted', gate.details));
    if (gate.command) {
      const code = el('pre', 'code-preview', gate.command);
      const copy = el('button', 'quiet-button', 'Copy instructions');
      copy.type = 'button';
      copy.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(gate.command); copy.textContent = 'Copied'; }
        catch (_) { copy.textContent = 'Clipboard unavailable — select the command above'; }
      });
      card.append(code, copy);
    }
    workspaceBody.appendChild(card);
  }
  workspaceBody.appendChild(el('p', 'muted', data.nonclaims.join(' ')));
}
