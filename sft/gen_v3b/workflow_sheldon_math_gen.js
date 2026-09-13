export const meta = {
  name: 'sheldon-math-gen',
  description: 'Generate Sheldon-voiced GSM8K-train rewrites, one subagent per 25-problem batch, each self-verified with verify_batch.py',
  phases: [{ title: 'Generate', detail: 'one agent per batch: write rows, run deterministic verifier, fix failures (<=3 runs)' }],
}
const DIR = args.dir
const batches = args.batches
const pad = n => String(n).padStart(3, '0')
const SCHEMA = {
  type: 'object',
  properties: {
    batch: { type: 'integer' }, n: { type: 'integer' }, pass: { type: 'integer' }, fail: { type: 'integer' },
    verify_runs: { type: 'integer' }, reasons: { type: 'object' }, notes: { type: 'string' },
  },
  required: ['batch', 'n', 'pass', 'fail', 'verify_runs'],
}
const prompt = b => `You are a data-generation worker. Working directory (contains a space, always quote it): "${DIR}"
Your batch: ${pad(b.id)}  (input: batches/batch_${pad(b.id)}.jsonl, output: out/batch_${pad(b.id)}.jsonl)

Steps:
1. Read "${DIR}/STYLE.md" completely and follow every rule in it.
2. Read "${DIR}/batches/batch_${pad(b.id)}.jsonl" (25 problems, one JSON per line).
3. For every row compose user_prompt (copy exactly for variant verbatim/eval; write it yourself for paraphrase, per STYLE.md) and the Sheldon response per the template. Write all rows, in order, as JSONL to "${DIR}/out/batch_${pad(b.id)}.jsonl" with keys id, user_prompt, response. Newlines inside strings must be JSON-escaped (\\n) and backslashes doubled (\\\\boxed). The safest way is a short Python script that holds the texts as Python string literals and json.dumps each row.
4. Run: cd "${DIR}" && python3 verify_batch.py --batch batches/batch_${pad(b.id)}.jsonl --out out/batch_${pad(b.id)}.jsonl
5. Rewrite ONLY the FAIL rows (fix the stated reasons; for bad_arithmetic recompute; for missing_intermediate include that value; for opener_dup change the first words), re-run the verifier. At most 3 verifier runs in total. Stop after that even if some rows still fail.
6. Return the structured result: batch=${b.id}, n, pass, fail, verify_runs, reasons (copy the numbers from the final "[verify] {...}" line exactly; never estimate), notes = one line on anything odd (ambiguous reference chains, checker false positives).

Rules: do not modify verify_batch.py, STYLE.md, or anything under batches/. Do not read or write other batches. Do not print the rows to your final answer; the file is the deliverable.`
phase('Generate')
const results = await pipeline(batches, b => {
  const opts = { label: `gen:${pad(b.id)}${b.model ? ':' + b.model : ''}`, phase: 'Generate', schema: SCHEMA }
  if (b.model) opts.model = b.model
  if (b.effort) opts.effort = b.effort
  return agent(prompt(b), opts)
})
const ok = results.filter(Boolean)
const reasons = {}
let pass = 0, n = 0
for (const r of ok) { pass += r.pass; n += r.n; for (const [k, v] of Object.entries(r.reasons || {})) reasons[k] = (reasons[k] || 0) + v }
const missing = batches.filter((b, i) => !results[i]).map(b => b.id)
log(`batches ${ok.length}/${batches.length} reported; rows pass ${pass}/${n}; missing ${JSON.stringify(missing)}`)
return { requested: batches.length, reported: ok.length, missing, n, pass, fail: n - pass, reasons, per_batch: ok }