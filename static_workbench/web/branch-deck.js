// BRANCH-DECK-001. Navigation only: never evaluates a ref, executes tests,
// fetches remotes, checks out a branch, or assumes that a cached ref is current.
let branchDeckSnapshot = null;
let branchDeckRemote = null;

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
  if (card.kind === 'github_remote') {
    host.appendChild(el('p', 'notice', `Observed on public GitHub at ${branchDeckRemote?.observed_at || 'unknown time'}; relation to local checkout: ${card.relation.replaceAll('_', ' ')}. Remote-only branches cannot be run locally until explicitly fetched and verified.`));
    if (card.open_prs?.length) {
      for (const pr of card.open_prs) {
        const a = el('a', 'quiet-button', `Open PR #${pr.number}: ${pr.title}${pr.draft ? ' [draft]' : ''}`);
        a.href = pr.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
        host.appendChild(a);
      }
    } else host.appendChild(el('p', 'muted tiny', card.pr_scan_complete ? 'No same-repository open PR observed for this branch in the checked scope.' : 'PR discovery was incomplete; absence is not established.'));
  }
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
  header.append(el('div', 'eyebrow', 'BRANCH INVENTORY / OBSERVATION ONLY'),
    el('h2', '', `${snapshot.branches.length} locally known refs · ${branchDeckRemote?.branches.length || 0} GitHub refs`),
    el('p', 'muted', 'Local and cached remote refs are shown separately from an explicitly requested public GitHub snapshot. No Git fetch, checkout, test execution, CI verdict, or merge permission.'));
  if (snapshot.gaps.length) {
    const warn = el('div', 'notice', `Incomplete inventory: ${snapshot.gaps.length} repositories were not fully scanned. No missing refs are implied to be absent.`);
    header.appendChild(warn);
    const gaps = el('div', 'muted tiny');
    gaps.textContent = snapshot.gaps.map(g => `${g.root_id}:${g.repo_path} (${g.reason})`).join(' · ');
    header.appendChild(gaps);
  }
  workspaceBody.appendChild(header);

  const remoteTools = el('section', 'card branch-deck-remote');
  remoteTools.appendChild(el('div', 'repo-name', 'Find branches that exist only on GitHub'));
  remoteTools.appendChild(el('p', 'muted', 'Select an existing local checkout with a public the-static-collective GitHub origin. This performs an explicit bounded public API lookup; it never fetches, installs, executes, or modifies repository content.'));
  const repoPicker = el('select');
  repoPicker.setAttribute('aria-label', 'Repository for public GitHub branch discovery');
  for (const item of state.repos) {
    const option = el('option', '', `${item.root_id}:${item.relative_path}`);
    option.value = JSON.stringify([item.root_id, item.relative_path]);
    repoPicker.appendChild(option);
  }
  const scan = el('button', 'action-button', 'Check public GitHub branches');
  scan.type = 'button'; scan.disabled = !state.repos.length;
  const remoteMessage = el('div', 'muted tiny', branchDeckRemote
    ? `Last selected GitHub observation: ${branchDeckRemote.github_repo} · ${branchDeckRemote.observed_at} · ${branchDeckRemote.gaps.length} scan gaps. Results are a dated snapshot, not a live subscription.`
    : 'Public remote lookup is opt-in in Workbench config, and runs only when you press this button.');
  scan.addEventListener('click', async () => {
    let chosen;
    try { chosen = JSON.parse(repoPicker.value); } catch (_) { return; }
    scan.disabled = true; remoteMessage.textContent = 'Checking the selected public GitHub repository…';
    try {
      const query = new URLSearchParams({root_id: chosen[0], repo_path: chosen[1]});
      const observed = await api('/api/branches/remote?' + query.toString());
      branchDeckRemote = observed;
      renderBranchDeck();
    } catch (error) {
      remoteMessage.textContent = error.message || String(error);
      scan.disabled = false;
    }
  });
  remoteTools.append(repoPicker, scan, remoteMessage);
  workspaceBody.appendChild(remoteTools);

  const controls = el('div', 'repo-tools branch-deck-controls');
  const search = el('input');
  search.type = 'search'; search.placeholder = 'Find repo, branch, or full SHA…';
  search.setAttribute('aria-label', 'Find branch');
  const filter = el('select');
  filter.setAttribute('aria-label', 'Branch filter');
  for (const [value, label] of [
    ['feature', 'Feature-like refs'], ['all', 'All refs'],
    ['local', 'Local branches'], ['cached_remote', 'Cached remote refs'],
    ['github_remote', 'Public GitHub branches'], ['remote_only', 'Not found locally'],
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
  const combined = [...snapshot.branches, ...(branchDeckRemote?.branches || [])];
  const sorted = combined.sort((a, b) =>
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
        (filter.value === 'remote_only' && card.relation === 'remote_only') ||
        (filter.value === 'other_worktree' && card.checkout === 'other_worktree') ||
        card.kind === filter.value;
      return match && scope;
    });
    count.textContent = `${visible.length} displayed / ${combined.length} observed refs`;
    if (!visible.length) list.appendChild(el('div', 'empty-state', 'No matching observed refs. Choose a configured repository and check GitHub to see unfetched branches.'));
    for (const card of visible) {
      const row = el('button', 'repo-row branch-deck-row');
      row.type = 'button';
      const left = el('div');
      left.append(el('div', 'repo-name', `${card.repo_name} / ${card.name}`),
        el('div', 'repo-meta', `${card.root_id}:${card.repo_path} · ${card.commit.slice(0, 12)} · ${card.committed_at || 'time unknown'}`),
        el('div', 'repo-meta', `${card.kind === 'github_remote' ? 'Public GitHub · ' + card.relation.replaceAll('_', ' ') : card.kind === 'cached_remote' ? 'Cached remote ref — freshness unknown' : 'Local branch'} · ${card.checkout.replaceAll('_', ' ')} · NOT TESTED`));
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
