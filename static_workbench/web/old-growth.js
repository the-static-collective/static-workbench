/* OLD-GROWTH-002: explicit local pinned Git source review -> native GRAFT ride. */
function oldGrowthMount(host) {
  const panel = el('section', 'card native-old-growth');
  panel.append(
    el('div', 'eyebrow', 'OLD GROWTH / PINNED HISTORICAL SOURCES'),
    el('h2', '', 'Compose two exact Git excerpts'),
    el('p', 'muted', 'Choose two locally discovered Collective repositories and exact commit/file/byte spans. Preview reads pinned Git objects, not your current working files. Local Git origin identity is descriptive, not remote authentication. Only selected excerpts enter the saved ride.')
  );
  const repos = state.repos.filter(repo => /^[0-9a-f]{40}$/.test(repo.head || '')
    && /^[A-Za-z0-9_.-]+$/.test(repo.name || '')
    && state.bootstrap.roots.some(root => root.id === repo.root_id));
  const form = el('form', 'native-spin-form');
  if (!repos.length) {
    panel.appendChild(el('div', 'notice', 'No checked-out repositories with a commit are visible. Configure a local root and refresh the repository inventory.'));
    host.appendChild(panel); return;
  }
  const sourceFields = [1, 2].map(number => {
    const wrap = el('fieldset', 'native-fuel-form');
    wrap.appendChild(el('legend', 'eyebrow', 'SOURCE ' + number + ' / DECLARED LOCAL CHECKOUT'));
    const label = el('label', 'native-fuel-form');
    label.appendChild(el('span', 'eyebrow', 'REPOSITORY'));
    const repoSelect = el('select'); repoSelect.setAttribute('aria-label', 'Old Growth source ' + number + ' repository');
    repos.forEach((repo, index) => {
      const option = el('option', '', repo.name + ' · ' + repo.root_id + ':' + repo.relative_path);
      option.value = String(index); repoSelect.appendChild(option);
    });
    if (number === 2 && repos.length > 1) repoSelect.value = '1';
    label.appendChild(repoSelect);
    const input = (name, placeholder, value, maxLength = 256) => {
      const field = el('label', 'native-fuel-form');
      field.appendChild(el('span', 'eyebrow', name));
      const element = el('input');
      element.required = true; element.maxLength = maxLength;
      element.placeholder = placeholder; element.value = value;
      element.setAttribute('aria-label', 'Old Growth source ' + number + ' ' + name);
      field.appendChild(element); wrap.appendChild(field);
      return element;
    };
    wrap.appendChild(label);
    const chosen = () => repos[Number(repoSelect.value)];
    const commit = input('PINNED COMMIT', '40-character lowercase Git SHA', chosen().head, 40);
    const path = input('RELATIVE TEXT PATH', 'README.md', 'README.md');
    const start = input('START BYTE (inclusive)', '0', '0', 8);
    const end = input('END BYTE (exclusive)', '512', '512', 8);
    start.type = 'number'; start.min = '0'; start.max = '131072';
    end.type = 'number'; end.min = '1'; end.max = '131072';
    repoSelect.addEventListener('change', () => { commit.value = chosen().head; });
    form.appendChild(wrap);
    return () => {
      const repo = chosen();
      return {
        root_id: repo.root_id,
        repo_path: repo.relative_path,
        repository: 'the-static-collective/' + repo.name,
        commit: commit.value.trim(), path: path.value.trim(),
        start_byte: Number(start.value), end_byte: Number(end.value),
      };
    };
  });
  const line = (name, placeholder, required = true) => {
    const field = el('label', 'native-fuel-form');
    field.appendChild(el('span', 'eyebrow', name));
    const box = el('textarea'); box.rows = 2; box.maxLength = 400; box.required = required;
    box.placeholder = placeholder; box.setAttribute('aria-label', 'Old Growth ' + name);
    field.appendChild(box); form.appendChild(field); return box;
  };
  const keep = line('KEEP', 'What must survive this crossing?');
  const bend = line('BEND', 'What might change without altering either parent?');
  const question = line('HUMAN QUESTION', 'What one reversible experiment would you like to propose?');
  const relation = el('select'); relation.setAttribute('aria-label', 'Old Growth human-declared relation');
  for (const lane of ['semantic', 'lineage', 'active_tension', 'human_link', 'rejected_parallel']) {
    const option = el('option', '', lane); option.value = lane; relation.appendChild(option);
  }
  const relationLabel = el('label', 'native-fuel-form');
  relationLabel.append(el('span', 'eyebrow', 'DECLARED RELATION (NOT INFERRED)'), relation);
  const move = el('select'); move.setAttribute('aria-label', 'Old Growth transformation');
  for (const name of ['fuse', 'invert', 'continue', 'wildcard']) {
    const option = el('option', '', name); option.value = name; move.appendChild(option);
  }
  const moveLabel = el('label', 'native-fuel-form');
  moveLabel.append(el('span', 'eyebrow', 'PROPOSED TRANSFORMATION'), move);
  const previewButton = el('button', 'action-button', 'Preview pinned source excerpts');
  previewButton.type = 'submit';
  const status = el('div', 'creator-feedback');
  const result = el('div', 'native-fuel-preview');
  form.append(relationLabel, moveLabel, previewButton, status);
  panel.append(form, result); host.appendChild(panel);
  const snapshot = () => ({
    source_a: sourceFields[0](), source_b: sourceFields[1](),
    keep: keep.value, bend: bend.value, question: question.value,
    relation_lane: relation.value, move: move.value,
  });
  let reviewed = null;
  form.addEventListener('input', () => { reviewed = null; clear(result); });
  form.addEventListener('change', () => { reviewed = null; clear(result); });
  form.addEventListener('submit', async event => {
    event.preventDefault(); reviewed = null; clear(status); clear(result);
    previewButton.disabled = true;
    try {
      const request = snapshot();
      const packet = await creatorV2Write('/api/house-maxhinal/old-growth/preview', request);
      reviewed = {request, packet};
      result.append(
        el('div', 'repo-name', 'Preview packet · SHA-256 ' + packet.packet_sha256),
        el('p', 'muted tiny', packet.review.instruction)
      );
      const marks = packet.packet.sources.map((source, index) => {
        const card = el('article', 'creator-preview-source');
        card.append(
          el('div', 'repo-name', 'SOURCE ' + (index + 1) + ' · ' + source.repository),
          el('div', 'muted tiny', source.commit + ' · ' + source.path +
            ' · UTF-8 bytes [' + source.start_byte + ', ' + source.end_byte + ')'),
          el('div', 'muted tiny', 'Local Git blob ' + source.git_blob_sha +
            ' · selected SHA-256 ' + source.excerpt_sha256),
          el('pre', 'raw-carrier', source.excerpt)
        );
        const mark = el('label', 'native-fuel-form');
        const input = el('input'); input.type = 'checkbox';
        input.setAttribute('aria-label', 'I reviewed Old Growth source ' + (index + 1));
        mark.append(input, el('span', '', 'I reviewed this exact source excerpt and locator.'));
        card.appendChild(mark); result.appendChild(card); return input;
      });
      const confirmLine = el('label', 'native-fuel-form');
      const confirm = el('input'); confirm.type = 'checkbox';
      confirm.setAttribute('aria-label', 'I confirm saving this Old Growth local ride');
      confirmLine.append(confirm, el('span', '',
        'Save ONLY selected excerpts as a Workbench-owned local ride. No project write, GRAFT selection or execution.'));
      const importButton = el('button', 'action-button', 'Import reviewed excerpts as one local GRAFT ride');
      importButton.type = 'button'; importButton.disabled = true;
      const updateEnabled = () => {
        importButton.disabled = !(marks.every(mark => mark.checked) && confirm.checked && reviewed);
      };
      marks.forEach(mark => mark.addEventListener('change', updateEnabled));
      confirm.addEventListener('change', updateEnabled);
      const importStatus = el('div', 'creator-feedback');
      importButton.addEventListener('click', async () => {
        importButton.disabled = true; clear(importStatus);
        if (!reviewed || marks.some(mark => !mark.checked) || !confirm.checked ||
            JSON.stringify(snapshot()) !== JSON.stringify(reviewed.request)) {
          nativeMaxhinalMessage(importStatus, 'Source/declarations changed or review is incomplete. Preview again.', true);
          return;
        }
        try {
          const saved = await creatorV2Write('/api/house-maxhinal/old-growth/import', {
            ...reviewed.request,
            expected_packet_sha256: reviewed.packet.packet_sha256,
            reviewed_excerpt_sha256: reviewed.packet.review.source_excerpt_sha256,
            human_confirmed: true,
          });
          nativeMaxhinalState.current = saved.ride;
          nativeMaxhinalState.rides = (await api('/api/house-maxhinal/rides')).rides;
          nativeMaxhinalRenderRide(); nativeMaxhinalRenderHistory();
          nativeMaxhinalMessage(importStatus, 'Local ride #' + saved.receipt.id +
            (saved.receipt.replayed ? ' already existed.' : ' saved.') +
            ' Open the GRAFT panel below to separately declare a round.');
        } catch (error) {
          nativeMaxhinalMessage(importStatus, error.message || String(error), true);
          updateEnabled();
        }
      });
      result.append(confirmLine, importButton, importStatus);
    } catch (error) {
      nativeMaxhinalMessage(result, error.message || String(error), true);
    } finally {
      previewButton.disabled = false;
    }
  });
}
