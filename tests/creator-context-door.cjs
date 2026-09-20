/* Pure planner regression tests for the browser-side Creator context door. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const code = fs.readFileSync(path.join(__dirname, '..', 'static_workbench', 'web',
  'creator-context-door.js'), 'utf8');
const propose = vm.runInNewContext(code + '\ncreatorContextProposal;');
const hashA = 'a'.repeat(64), hashB = 'b'.repeat(64);
const pack = {
  id: 7, pack_sha256: hashA,
  sources: [
    { root_id: 'local', repo_path: 'song', source_path: 'lyrics.txt',
      line_start: 2, file_sha256: hashA },
    { root_id: 'local', repo_path: 'song', source_path: 'notes.txt',
      line_start: 6, file_sha256: hashB },
  ],
};
const a = propose(pack, [0], 'follow');
const b = propose(pack, [0], 'contrast');
assert.equal(a.status, 'preview-only-not-saved');
assert.equal(a.sends.length, 1);
assert.equal(a.sends[0].response, 'follow');
assert.equal(b.sends[0].response, 'contrast');
assert.equal(a.sends[0].source_ref, 'local:song/lyrics.txt#L2');
assert.equal(JSON.stringify(a.ignored), '[1]');
assert.equal(propose(pack, [1, 0], 'follow').sends[0].index, 0);
assert.equal(a.pack_sha256, hashA);
assert.equal(Object.isFrozen(a.sends), true);
assert.equal('source_bytes' in a, false);
for (const input of [
  () => propose(pack, [], 'follow'),
  () => propose(pack, [0, 0], 'follow'),
  () => propose(pack, [3], 'follow'),
  () => propose(pack, [0], 'execute'),
  () => propose({...pack, pack_sha256: 'stale'}, [0], 'follow'),
  () => propose({...pack, sources: [pack.sources[0], {...pack.sources[1], file_sha256: 'invalid'}]}, [1], 'follow'),
]) {
  assert.throws(input);
}
console.log('Creator contextual composition planner: PASS');
