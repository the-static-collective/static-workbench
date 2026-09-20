/* HOUSE Staged Rocket v0.1 — no arbitrary commands, no automatic children. */
const rocketState = { catalog: null, missions: [], current: null, parent: null };

async function rocketWrite(path, payload) {
  return api(path, {
    method: 'POST',
    headers: { 'X-Workbench-Session': state.bootstrap.session_token },
    ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
  });
}
function rocketField(host, label, multiline, limit, required = false) {
  const wrap = el('label', 'rocket-field');
  wrap.appendChild(el('span', 'muted tiny', label));
  const input = el(multiline ? 'textarea' : 'input');
  input.maxLength = limit;
  input.required = required;
  if (multiline) input.rows = 3;
  wrap.appendChild(input);
  host.appendChild(wrap);
  return input;
}
function rocketError(host, error) {
  host.className = 'notice error';
  host.textContent = error.message || String(error);
}
function rocketOption(select, value, label) {
  const option = el('option', '', label);
  option.value = value;
  select.appendChild(option);
}
async function rocketLoad() {
  const [catalog, listing] = await Promise.all([
    api('/api/rockets/catalog'), api('/api/rockets/missions'),
  ]);
  rocketState.catalog = catalog;
  rocketState.missions = listing.missions;
  if (rocketState.current) rocketState.current = await api('/api/rockets/missions/' + rocketState.current.id);
  if (state.view === 'rocket') rocketRender();
}
async function rocketOpen(id) {
  rocketState.current = await api('/api/rockets/missions/' + id);
  rocketRender();
}
async function rocketAdvance(mission, action, payload, feedback, button) {
  button.disabled = true;
  try {
    await rocketWrite('/api/rockets/missions/' + mission.id + '/' + action, payload);
    await rocketOpen(mission.id);
    await rocketLoad();
    await loadEvents();
  } catch (error) {
    rocketError(feedback, error);
    button.disabled = false;
  }
}
function rocketRender() {
  state.view = 'rocket';
  syncNav('rocket');
  setWorkspace('Staged Rocket', 'Compose · Verify · Grow');
  clear(workspaceBody);

  const intro = el('section', 'card rocket-panel');
  intro.append(
    el('div', 'eyebrow', 'TEMPORARY COMPOSITION / NO AUTOMATIC DISPATCH'),
    el('h2', '', 'One mission. Three receipts. A possible next mission.'),
    el('p', 'muted', 'Prepare pins clean local repositories. Execute runs one allowlisted read-only operation. Separate records your proposed next action. Launching a descendant always requires a new, explicit mission.'),
  );
  workspaceBody.appendChild(intro);

  const catalog = rocketState.catalog;
  if (!catalog) { workspaceBody.appendChild(el('div', 'muted', 'Tool catalog unavailable.')); return; }
  const create = el('section', 'card rocket-panel');
  create.appendChild(el('h2', '', 'Declare a mission'));
  if (rocketState.parent) {
    const parentNote = el('div', 'notice', 'New mission references separated mission #' + rocketState.parent.id + ' · ' + rocketState.parent.sha256.slice(0, 16) + '… . This reference does not authorize the new mission.');
    const detach = el('button', 'quiet-button', 'Start unrelated mission');
    detach.type = 'button';
    detach.addEventListener('click', () => { rocketState.parent = null; rocketRender(); });
    create.append(parentNote, detach);
  }
  const form = el('form', 'rocket-form');
  const title = rocketField(form, 'Mission title', false, 160, true);
  const purpose = rocketField(form, 'One bounded purpose', true, 2000, true);
  const modeWrap = el('label', 'rocket-field');
  modeWrap.appendChild(el('span', 'muted tiny', 'Operation to execute'));
  const mode = el('select');
  rocketOption(mode, 'source-preview', 'Source preview · one repository');
  rocketOption(mode, 'body-overlap', 'BODY interface comparison · two repositories');
  if (rocketState.parent?.nativeSeedId) rocketOption(mode, 'creator-seed-preview', 'Consume exact parent Creator seed · no repository');
  modeWrap.appendChild(mode); form.appendChild(modeWrap);
  const available = catalog.repos.filter(r => r.selectable);
  const repoA = el('select'), repoB = el('select');
  const makeRepoField = (caption, field) => {
    const wrap = el('label', 'rocket-field');
    wrap.appendChild(el('span', 'muted tiny', caption));
    rocketOption(field, '', 'Select an observed clean checkout');
    available.forEach((r, index) => rocketOption(
      field, String(index), r.root_id + ':' + r.repo_path + ' · ' + r.expected_sha.slice(0, 12),
    ));
    wrap.appendChild(field); form.appendChild(wrap);
    return wrap;
  };
  const first = makeRepoField('First source', repoA);
  const second = makeRepoField('Second source', repoB);
  const path = rocketField(form, 'Repository-relative source file (.md / .txt / .json / .toml)', false, 300);
  const updateMode = () => {
    first.hidden = mode.value === 'creator-seed-preview';
    second.hidden = mode.value !== 'body-overlap';
    path.parentNode.hidden = mode.value !== 'source-preview';
    path.required = mode.value === 'source-preview';
  };
  if (rocketState.parent?.nativeSeedId) mode.value = 'creator-seed-preview';
  mode.addEventListener('change', updateMode); updateMode();
  const submit = el('button', 'action-button', 'Save inert mission plan');
  submit.type = 'submit';
  submit.disabled = !available.length && !rocketState.parent?.nativeSeedId;
  const feedback = el('div');
  form.append(submit, feedback);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    submit.disabled = true;
    try {
      if (mode.value !== 'creator-seed-preview' && (repoA.value === '' || (mode.value === 'body-overlap' && repoB.value === ''))) {
        throw new Error('Explicitly select the source checkout(s).');
      }
      const inputs = mode.value === 'creator-seed-preview' ? [] : [available[Number(repoA.value)]];
      if (mode.value === 'body-overlap') inputs.push(available[Number(repoB.value)]);
      const selections = inputs.map(r => ({
        root_id: r.root_id, repo_path: r.repo_path, expected_sha: r.expected_sha,
      }));
      const payload = {
        title: title.value, purpose: purpose.value, mode: mode.value,
        selections, source_path: mode.value === 'source-preview' ? path.value : '',
        ...(mode.value === 'creator-seed-preview' ? {
          creator_seed_id: rocketState.parent.nativeSeedId,
          expected_creator_sha256: rocketState.parent.nativeSeedSha256,
        } : {}),
        ...(rocketState.parent ? {
          parent_id: rocketState.parent.id,
          expected_parent_sha256: rocketState.parent.sha256,
        } : {}),
      };
      const mission = await rocketWrite('/api/rockets/missions', payload);
      rocketState.current = mission;
      rocketState.parent = null;
      await rocketLoad();
      await loadEvents();
    } catch (error) {
      rocketError(feedback, error);
      submit.disabled = false;
    }
  });
  create.appendChild(form);
  workspaceBody.appendChild(create);

  const listing = el('section', 'card rocket-panel');
  listing.appendChild(el('h2', '', 'Recover previous missions'));
  if (!rocketState.missions.length) listing.appendChild(el('p', 'muted', 'No declared missions yet.'));
  rocketState.missions.forEach(m => {
    const button = el('button', 'quiet-button rocket-history', '#' + m.id + ' · ' + m.title + ' · ' + m.completed_stages + '/3 stages');
    button.type = 'button';
    button.addEventListener('click', () => rocketOpen(m.id).catch(showError));
    listing.appendChild(button);
  });
  workspaceBody.appendChild(listing);

  const mission = rocketState.current;
  if (!mission) return;
  const active = el('section', 'card rocket-panel');
  active.append(
    el('div', 'eyebrow', 'MISSION #' + mission.id + ' · ' + mission.mode),
    el('h2', '', mission.title),
    el('p', '', mission.purpose),
    el('div', 'muted tiny rocket-digest', 'Mission SHA-256 ' + mission.mission_sha256),
    el('div', 'muted tiny', 'Parent: ' + (mission.parent_id ? '#' + mission.parent_id + ' · ' + mission.parent_sha256 : '(root mission)')),
  );
  const stages = mission.stages;
  if (stages.length === 0) {
    const start = el('button', 'action-button', 'Stage 1 · Prepare exact source observations');
    start.type = 'button';
    const feedback = el('div');
    start.addEventListener('click', () => rocketAdvance(mission, 'prepare', undefined, feedback, start));
    active.append(start, feedback);
  }
  if (stages.length === 1) {
    active.appendChild(el('p', 'muted', 'Stage 1 has been recorded. Source state will be checked again before execution.'));
    const run = el('button', 'action-button', 'Stage 2 · Execute selected read-only operation');
    run.type = 'button';
    const feedback = el('div');
    run.addEventListener('click', () => rocketAdvance(mission, 'execute',
      { expected_stage_sha256: stages[0].sha256 }, feedback, run));
    active.append(run, feedback);
  }
  if (stages.length === 2) {
    const form = el('form', 'rocket-form');
    const next = rocketField(form, 'What new action does this result make worth testing?', true, 2000, true);
    const fog = rocketField(form, 'Remaining gaps or unproven assumptions', true, 2000);
    const button = el('button', 'action-button', 'Stage 3 · Separate and preserve mission seed');
    button.type = 'submit';
    const feedback = el('div');
    form.append(button, feedback);
    form.addEventListener('submit', async event => {
      event.preventDefault();
      await rocketAdvance(mission, 'separate', {
        expected_stage_sha256: stages[1].sha256,
        next_action: next.value, residual_fog: fog.value,
      }, feedback, button);
    });
    active.appendChild(form);
  }
  if (stages.length === 3) {
    active.appendChild(el('div', 'notice', 'All three inspection stages are preserved. No project action has run automatically.'));
    if (mission.effect) {
      const result = el('section', 'rocket-stage');
      result.append(
        el('h3', '', 'Owner-native effect confirmed'),
        el('p', 'muted', 'Creator Desk seed #' + mission.effect.output.native_seed_id +
          ' was saved locally. This receipt does not claim that an external project was modified.'),
        el('div', 'muted tiny rocket-digest', 'Effect SHA-256 ' + mission.effect.receipt_sha256),
      );
      const inspect = el('button', 'quiet-button', 'Inspect saved Creator seed');
      inspect.type = 'button';
      inspect.addEventListener('click', async () => {
        try {
          const seed = await api('/api/creator/rocket-seeds/' + mission.effect.output.native_seed_id);
          result.appendChild(el('pre', 'raw-carrier rocket-output', JSON.stringify(seed, null, 2)));
          inspect.disabled = true;
        } catch (error) { showError(error); }
      });
      result.appendChild(inspect);
      active.appendChild(result);
    } else if (mission.mode === 'source-preview' || mission.mode === 'creator-seed-preview') {
      const owner = el('section', 'rocket-stage');
      owner.appendChild(el('h3', '', 'Flight Two · Save one real Creator Desk seed'));
      owner.appendChild(el('p', 'muted',
        'Only HOUSE Creator Desk storage will change. Read the proposed text, explicitly authorize the local save, and keep the original source separate.'));
      const form = el('form', 'rocket-form');
      const title = rocketField(form, 'New seed title', false, 160, true);
      title.value = mission.title + ' — proposed continuation';
      const body = rocketField(form, 'Human-reviewed proposed content (not original source)', true, 8000, true);
      body.value = stages[2].output.next_action_proposed_by_human;
      const consentWrap = el('label', 'rocket-field');
      const consent = el('input'); consent.type = 'checkbox'; consent.required = true;
      consentWrap.append(consent, el('span', '', 'I authorize this exact proposed text to be saved as a HOUSE-local Creator Desk seed. No source repository write or publication.'));
      form.appendChild(consentWrap);
      const save = el('button', 'action-button', 'Authorize and save Creator seed');
      save.type = 'submit';
      const feedback = el('div');
      form.append(save, feedback);
      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (!consent.checked) return;
        save.disabled = true;
        try {
          await rocketWrite('/api/rockets/missions/' + mission.id + '/launch-creator-seed', {
            expected_stage_sha256: stages[2].sha256, target: 'creator.seed/v0',
            authorization: 'save_creator_seed', title: title.value, body: body.value,
          });
          await rocketOpen(mission.id);
          await rocketLoad();
          await loadEvents();
        } catch (error) { rocketError(feedback, error); save.disabled = false; }
      });
      owner.appendChild(form); active.appendChild(owner);
    }
    const child = el('button', 'action-button', 'Declare a new rocket from this result');
    child.type = 'button';
    child.addEventListener('click', () => {
      rocketState.parent = { id: mission.id, sha256: mission.effect
        ? mission.effect.receipt_sha256 : stages[2].sha256,
        ...(mission.effect ? {
          nativeSeedId: mission.effect.output.native_seed_id,
          nativeSeedSha256: mission.effect.output.native_content_sha256,
        } : {}),
      };
      rocketState.current = null;
      rocketRender();
    });
    active.appendChild(child);
  }
  const chain = el('div', 'rocket-stage-chain');
  stages.slice().reverse().forEach(stage => {
    const receipt = el('article', 'rocket-stage');
    receipt.append(
      el('div', 'eyebrow', 'STAGE ' + stage.ordinal + ' / ' + stage.kind + ' · ' + stage.created_at),
      el('pre', 'raw-carrier rocket-output', JSON.stringify(stage.output, null, 2)),
      el('div', 'muted tiny rocket-digest', 'SHA-256 ' + stage.sha256 + ' · previous ' + (stage.previous_sha256 || '(root)')),
    );
    chain.appendChild(receipt);
  });
  active.appendChild(chain);
  workspaceBody.appendChild(active);
}
