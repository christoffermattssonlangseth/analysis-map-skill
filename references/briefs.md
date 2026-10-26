# Agent briefs

Copy a brief into an Agent prompt, fill the <placeholders>, and run agents in parallel on disjoint slices. Every brief
shares three rules, because the map is shown to collaborators who will trust it:
1. Facts only from the named sources; never invent a number, method detail or result. Missing → say so.
2. Give each agent its own working folder and output file (agents sharing a scratch folder overwrote each other).
3. Ask for a short report of conflicts between sources - these are often real errors in the project worth fixing.

## Catalogue (only if the project has no run catalogue)
> Build a run catalogue for the repo at <repo>. A "run" is one analysis that answers one question (a script or notebook
> section with its own outputs). Survey analysis/, scripts/, notebooks/, results folders and docs; for <slice of the
> repo>, write one entry per run in the format in <skill>/references/inputs.md ("Run catalogue"): a one-sentence finding
> as the title, the header line naming notebook, code, results and figures, then Rationale (from docs, commit messages,
> docstrings), Technical approach (from the code: data, unit, preprocessing, model, folds, controls), Results (from the
> output files, numbers exact), Caveats. Number entries in rough chronological order starting at <N>. Write to
> <path>. Report runs you could not document and why.

## Runs table
> For each entry §<a>–§<b> in <catalogue>, write one CSV row: section, short_title (≤12 words, plain English), group
> (one of: <list of approach groups, or "propose 10-15 groups">), method (≤12 words), unit (unit of analysis/inference),
> validation (≤10 words), data, key_result (≤28 words with the headline number), status (exactly one of <vocabulary>).
> Read each entry's Results/Reading/Caveats, not only the title; if a later entry corrects it, say so in key_result.
> Write <path>.csv with Python's csv module. Report row count per group and any judgement calls.

## Registry (optional)
> For every section in <catalogue>, trace the run in code and write one row of <path>/pipeline-registry.csv with:
> section, short_title, group, scripts, input_data, preprocessing (normalisation/aggregation actually in code), inputs,
> target (and what is held out of the inputs), model (estimator + key settings), split (fold scheme and unit; say
> whether samples from one subject can straddle train/test), evaluation (metric, null, replication rule), result,
> outputs, notebook, status, trace_confidence (high = read in code, medium = docstring/catalogue, low = inferred),
> leak_flag (none/possible/yes), notes (every code-catalogue mismatch). Also write <path>/pipeline.md: a 2-page guide
> for ML collaborators (units, standard folds, shared preprocessing, data objects, how to trace a result). Report
> leakage and code-catalogue disagreements first.

## Plain language
> Write reader-friendly explanations for runs <list or range> of <catalogue>. Sources: the catalogue entry (check
> later entries for corrections), <registry> row, the run's scripts (docstring and key code), small result files.
> For each run write two markdown pieces: "how" (120-220 words): what data went in and at what unit, how it was
> prepared, what was predicted or compared, what the model/statistic does in one plain sentence, how it was checked and
> WHY each control rules out the obvious alternative; define jargon once ("leave-one-animal-out: train on all but one,
> test on the one left out"). "results" (120-250 words): the main numbers with what each means in words, comparison to
> control/baseline, what held and what did not, later corrections. Plain direct sentences (<25 words), no headings, at
> most 2-3 bold phrases, no em-dash asides. Project context: <2-3 sentences: field, main dataset, units>.
> Output {"<n>": {"how": "...", "results": "..."}} to <path>.json; validate it parses.

## Legends
> Write figure legends. Input <path>/todo_legends_part<k>.json: keys are image paths relative to <build_dir>; values
> give the runs and either notebook context (plotting cell `code`, `md_before`, `md_after`) or the source `file`.
> For EVERY image: open it with the Read tool and look at it; read its context and, if needed, the run's catalogue
> entry. Write: **<short title stating what the figure shows or finds.>** then 2-4 plain sentences: what is plotted
> (axes, units, what a point/bar/colour/panel is, the unit of a point), the comparison or control shown, what to notice.
> Numbers only if visible or stated in the sources. If unreadable: "**Figure not interpretable.**" + why. Save progress
> every ~15 figures. Output {"figs/x.jpg": "legend"} to <path>/legends_part<k>.json. Report: count, unreadable ones,
> and figures whose content belongs to a different run (key, current run, better run, why).

## Splitting work
`todo_legends.json` → split into parts with ~90 keys sorted by run, so one agent sees related figures together:
```python
import json; m = json.load(open("todo_legends.json")); keys = sorted(m, key=lambda s: (min(m[s]["runs"]), s))
n = 5; size = -(-len(keys) // n)
for i in range(n): json.dump({k: m[k] for k in keys[i*size:(i+1)*size]}, open(f"todo_legends_part{i+1}.json", "w"))
```

## Group summaries
> Write summary cards for approach groups <names>. Input: a JSON per group with its runs (section, title, status,
> key_result, plain results, figures with src + legend); images at <build_dir>/<src>; the catalogue for corrections.
> Per group: "summary" 90-150 plain words (what the runs asked, the 2-3 main numbers and what they mean, what failed
> or was corrected, how confident; name runs as §N; at most 2 bold phrases; no invented numbers) and "figs": 2-4 src
> values from the group's runs that best show its findings, from different runs where possible. Open every chosen
> image and confirm it is readable and shows the claim. Output {"<group>": {"summary": ..., "figs": [...]}}; validate.
