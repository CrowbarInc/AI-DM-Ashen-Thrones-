/* Offline unit check of form code with a minimal DOM stub; no rendered-browser claim. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(require('node:path').join(__dirname, 'review.html'), 'utf8');
const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.equal(scripts.length, 2);
const blank = JSON.parse(scripts[0]);
const articles = blank.turns.map(t => {
  const fields = Object.keys(t).filter(k => k !== 'review_id').map(name => ({name, value: '', options: []}));
  return {dataset: {reviewId: t.review_id}, querySelectorAll: selector => selector === 'select' ?
    fields.filter(e => e.name !== 'reviewer_explanation') : fields, fields};
});
// Read actual allowed option values from each article, not a second hardcoded rubric.
const articleMarkup = [...html.matchAll(/<article data-review-id="([^"]+)">([\s\S]*?)<\/article>/g)];
assert.equal(articleMarkup.length, 37);
articleMarkup.forEach(([, id, content], i) => {
  assert.equal(id, articles[i].dataset.reviewId);
  const selects = [...content.matchAll(/<select name="([^"]+)">([\s\S]*?)<\/select>/g)];
  assert.equal(selects.length, 6);
  selects.forEach(([, name, opts]) => {
    const field = articles[i].fields.find(e => e.name === name);
    field.options = [...opts.matchAll(/<option value="([^"]*)">/g)].map(m => ({value: m[1]}));
    assert.equal(field.options[0].value, '');
  });
});
const nodes = Object.fromEntries(['reviewer', 'reviewed_at', 'attestation', 'export', 'import', 'status'].map(k =>
  ['#' + k, {value: '', checked: false, textContent: ''}]));
nodes['#blank'] = {textContent: scripts[0]};
blank.conversations.forEach(c => nodes[`[data-conversation="${c.scenario_id}"]`] = {value: ''});
let downloads = 0;
const document = {
  querySelector: s => {assert.ok(nodes[s], 'Unknown selector ' + s); return nodes[s];},
  querySelectorAll: s => {assert.equal(s, 'article'); return articles;},
  createElement: tag => {assert.equal(tag, 'a'); return {click() {assert.equal(this.download, 'human_judgments.json'); downloads++;}};}
};
const context = vm.createContext({document, structuredClone, Blob,
  URL: {createObjectURL: () => 'mock-object-url', revokeObjectURL: () => {}}, setTimeout: fn => fn()});
vm.runInContext(scripts[1], context);
const collect = () => JSON.parse(JSON.stringify(vm.runInContext('collect()', context)));
assert.deepEqual(collect(), blank);
nodes['#export'].onclick();
assert.equal(downloads, 1);
(async () => {
  const resumed = structuredClone(blank);
  resumed.reviewer = 'SYNTHETIC FORM UNIT TEST';
  resumed.turns[0].reviewer_explanation = 'A multiline test\n<&> preserved, no gameplay judgment.';
  resumed.conversations[0].qualitative_observations = 'Synthetic form text only.';
  await nodes['#import'].onchange({target: {files: [{text: async () => JSON.stringify(resumed)}]}});
  assert.deepEqual(collect(), resumed);
  const invalid = structuredClone(resumed);
  invalid.turns[0].review_id = 'S04.1/trial-1';
  await nodes['#import'].onchange({target: {files: [{text: async () => JSON.stringify(invalid)}]}});
  assert.match(nodes['#status'].textContent, /Import refused/);
  assert.deepEqual(collect(), resumed);
  console.log('PASS: blank controls, collect/export/import roundtrip, exact trial validation; offline DOM stub only.');
})().catch(e => {console.error(e);process.exitCode=1;});
