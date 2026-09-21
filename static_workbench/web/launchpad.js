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
  // FLIGHT-BOARD-001: explicit navigation only; never infer repository readiness
  // or execute a project merely because it was discovered.
  const firstUse = el('section', 'card');
  firstUse.append(
    el('div', 'eyebrow', 'WORKBENCH FIRST FLIGHT · LOCAL ONLY'),
    el('h2', '', 'Start with what is already in the house'),
    el('p', 'muted', 'Choose a desk below. Opening a desk is not permission to run an external project. Source selection, creative saves, tests and project effects keep their separate approval gates.')
  );
  const available = el('div', 'action-grid');
  const destinations = [
    ['Discover my projects', 'Inspect observed checkouts; presence is not installation or readiness.', () => renderRepos()],
    ['Find a feature branch', 'Inspect branch ancestry and explicitly select an isolated local test.', () => branchDeckOpen().catch(showError)],
    ['Make a new creative draft', 'Select a local source pack, shape a creative direction and save only when you choose.', () => { renderCreatorDesk(); creatorV2Load().catch(showError); }],
    ['Open the Maxhinal', 'Preview a bounded composition using explicitly selected local fuel.', () => { renderNativeMaxhinal(); nativeMaxhinalLoad().catch(showError); }],
    ['Inspect my returns', 'Resume recorded work; reported project effects remain unverified.', () => returnDeskLoad().catch(showError)],
    ['See attention marks', 'Open the local Attention Shelf without sending marks to another project.', () => { state.view = 'attention'; window.HumanValueBar.openShelf().catch(showError); }],
    ['Explore MIRROR', 'Edit only the owned demo fixture using a separate reviewed apply.', () => renderMirror().catch(showError)],
    ['Try the field lab', 'Run synthetic GROUNDKEEPER experiments, not physical sensor capture.', () => groundkeeperView()]
  ];
  for (const [label, description, open] of destinations) {
    const card = el('button', 'action-card');
    card.type = 'button';
    card.append(el('strong', '', label), el('span', 'muted', description));
    card.addEventListener('click', open);
    available.appendChild(card);
  }
  firstUse.appendChild(available);
  workspaceBody.appendChild(firstUse);
  const inventoryCard = el('section', 'card');
  inventoryCard.append(
    el('div', 'eyebrow', 'ARK / ARRIVAL · OBSERVATION ONLY'),
    el('h2', '', 'Neighboring project organs')
  );
  try {
    const arrival = await api('/api/arrival');
    if (state.view !== 'launchpad') return;
    const observed = arrival.organs.filter(organ => organ.observed === 'checkout_observed');
    inventoryCard.appendChild(el('p', 'muted',
      observed.length + ' of ' + arrival.organs.length + ' optional organs have a discovered local checkout. Neither discovery nor a matching name establishes installed, compatible, ready or authorized status.'));
    for (const organ of arrival.organs) {
      const count = organ.checkouts.length;
      const note = count === 0 ? 'not discovered' : count === 1 ? 'one checkout observed' : 'multiple checkouts — select explicitly';
      inventoryCard.appendChild(el('p', 'muted tiny', organ.id + ' · ' + note + ' · ready: not evaluated'));
    }
  } catch (error) {
    inventoryCard.appendChild(el('p', 'muted', 'Local inventory could not be read: ' + (error.message || String(error))));
  }
  workspaceBody.appendChild(inventoryCard);
  workspaceBody.appendChild(el('h2', '', 'STATIC OS · separately gated experiments'));
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
