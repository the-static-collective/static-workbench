// BRANCH-DECK-001. Navigation only: never evaluates a ref, executes tests,
// fetches remotes, checks out a branch, or assumes that a cached ref is current.
let branchDeckSnapshot = null;

async function loadBranchDeck() {
  const snapshot = await api('/api/branches');
  branchDeckSnapshot = snapshot;
  const count = document.querySelector('#branch-count');
  if (count) count.textContent = String(snapshot.branches.length) + (snapshot.gaps.length ? '+' : '');
  if (state.view === 'branches') renderBranchDeck();
  else if (state.view === 'house') renderHouse();
}

function branchDeckTeaser() {
  const card = el('section', 'card branch-deck-teaser');
  const title = el('div', 'repo-name', 'Branch Deck / development surfaces');
  const snapshot = branchDeckSnapshot;
  const message = snapshot
    ? `${snapshot.branches.length} known refs in ${snapshot.repos_scanned} local repositories · ${snapshot.gaps.length} incomplete scans`
    : 'Discover every locally known branch, not just the checked-out one.';
  const note = el('div', 'muted tiny', message);
  const open = el('button', 'action-button', 'Open Branch Deck');
  open.type = 'button';
  open.addEventListener('click', () => branchDeckOpen().catch(showError));
  card.append(title, note, open);
  return card;
}

async function branchDeckOpen() {
  state.view = 'branches';
  syncNav('branches');
  if (!branchDeckSnapshot) await loadBranchDeck();
  renderBranchDeck();
}

function branchDeckPlan(card, host) {
  clear(host);
  host.append(
    el('div', 'repo-name', `${card.repo_name} / ${card.name}`),
    el('div', 'repo-meta', `Exact observed commit: ${card.commit}`),
    el('p', 'muted', 'Manual isolated test route: confirm the exact ref and commit, create a separate Git worktree with Git, inspect the branch-owned setup instructions, then choose and run the project’s approved tests yourself. Keep the original checkout and main untouched. Record the test command, environment, result, and exact commit before integration.')
  );
  if (card.kind === 'cached_remote') {
    host.appendChild(el('p', 'notice', 'This is a locally cached remote-tracking ref. It may be stale; verify/fetch through a separately authorized workflow before testing.'));
  }
  const matching = state.repos.find(item => item.root_id === card.root_id && item.relative_path === card.repo_path);
  if (matching) {
    const inspect = el('button', 'quiet-button', 'Inspect current repository checkout');
    inspect.type = 'button';
    inspect.addEventListener('click', () => renderRepoDetail(matching));
    host.appendChild(inspect);
  }
}

function renderBranchDeck() {
  state.view = 'branches'; syncNav('branches');
  setWorkspace('Branch Deck', 'Find the next working surface');
  clear(workspaceBody);
  const snapshot = branchDeckSnapshot;
  if (!snapshot) {
    workspaceBody.appendChild(el('div', 'empty-state', 'Branch inventory has not loaded. Use Refresh.'));
    return;
  }
  const header = el('section', 'card');
  header.append(el('div', 'eyebrow', 'LOCAL REFS / NAVIGATION ONLY'),
    el('h2', '', `${snapshot.branches.length} known branches · ${snapshot.repos_scanned} repositories`),
    el('p', 'muted', 'Local branches and cached remote-tracking refs only. No network fetch, new-branch claim, test execution, checkout, CI result, PR association, readiness verdict, or merge permission.'));
  if (snapshot.gaps.length) {
    const warn = el('div', 'notice', `Incomplete inventory: ${snapshot.gaps.length} repositories were not fully scanned. No missing refs are implied to be absent.`);
    header.appendChild(warn);
    const gaps = el('div', 'muted tiny');
    gaps.textContent = snapshot.gaps.map(g => `${g.root_id}:${g.repo_path} (${g.reason})`).join(' · ');
    header.appendChild(gaps);
  }
  workspaceBody.appendChild(header);

  const controls = el('div', 'repo-tools branch-deck-controls');
  const search = el('input');
  search.type = 'search'; search.placeholder = 'Find repo, branch, or full SHA…';
  search.setAttribute('aria-label', 'Find branch');
  const filter = el('select');
  filter.setAttribute('aria-label', 'Branch filter');
  for (const [value, label] of [
    ['feature', 'Feature-like refs'], ['all', 'All refs'],
    ['local', 'Local branches'], ['cached_remote', 'Cached remote refs'],
    ['other_worktree', 'Open in another worktree'],
  ]) {
    const option = el('option', '', label);
    option.value = value;
    filter.appendChild(option);
  }
  const count = el('div', 'muted tiny');
  controls.append(search, filter, count);
  workspaceBody.appendChild(controls);
  const list = el('div', 'repo-list');
  workspaceBody.appendChild(list);
  const detail = el('section', 'card branch-deck-detail');
  detail.appendChild(el('div', 'muted', 'Choose a branch for its exact commit and isolated test route.'));
  workspaceBody.appendChild(detail);
  const sorted = [...snapshot.branches].sort((a, b) =>
    Number(b.feature_like) - Number(a.feature_like) ||
    a.repo_name.localeCompare(b.repo_name) || a.name.localeCompare(b.name) ||
    a.kind.localeCompare(b.kind));
  function draw() {
    clear(list);
    const needle = search.value.trim().toLowerCase();
    const visible = sorted.filter(card => {
      const match = !needle || [card.root_id, card.repo_path, card.repo_name, card.name, card.commit]
        .some(value => String(value || '').toLowerCase().includes(needle));
      const scope = filter.value === 'all' ||
        (filter.value === 'feature' && card.feature_like) ||
        (filter.value === 'other_worktree' && card.checkout === 'other_worktree') ||
        card.kind === filter.value;
      return match && scope;
    });
    count.textContent = `${visible.length} displayed / ${snapshot.branches.length} known refs`;
    if (!visible.length) list.appendChild(el('div', 'empty-state', 'No matching locally known refs. Remote-only branches require a separate authorized fetch.'));
    for (const card of visible) {
      const row = el('button', 'repo-row branch-deck-row');
      row.type = 'button';
      const left = el('div');
      left.append(el('div', 'repo-name', `${card.repo_name} / ${card.name}`),
        el('div', 'repo-meta', `${card.root_id}:${card.repo_path} · ${card.commit.slice(0, 12)} · ${card.committed_at || 'time unknown'}`),
        el('div', 'repo-meta', `${card.kind === 'cached_remote' ? 'Cached remote ref — freshness unknown' : 'Local branch'} · ${card.checkout.replaceAll('_', ' ')} · NOT TESTED`));
      const badge = el('span', 'state-pill', card.feature_like ? 'feature-like' : 'branch');
      row.append(left, badge);
      row.addEventListener('click', () => branchDeckPlan(card, detail));
      list.appendChild(row);
    }
  }
  search.addEventListener('input', draw);
  filter.addEventListener('change', draw);
  draw();
}
