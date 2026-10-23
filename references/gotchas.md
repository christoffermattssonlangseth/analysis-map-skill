# Gotchas from the first build

**D3 `.call(fn).text(...)` erases the node.** `selection.call(fn)` returns the *original* selection, so a following
`.text()` set text on the node's `<g>` and wiped its circle and label: every group and run node vanished while the links
still drew. Use `fn(selection).text(...)` where `fn` returns the appended `<text>`. Symptom: branches end in nothing.

**`[hidden]` vs `display:flex`.** A class that sets `display:flex` beats the `hidden` attribute. The published Artifact
skeleton adds `[hidden]{display:none!important}`, a standalone file does not - the template sets it itself.

**Radial layout crowding.** `d3.cluster` gives goals with few runs tiny angles, so their labels collide. The template
assigns each goal a sector proportional to max(run count, 11) and each group max(run count, 4).

**Overview fit.** Fit the overview to the rings (run labels are hidden at overview), not to label extents, or the map
renders tiny. Focused views need more top margin for outward run labels.

**Figures keyed by source-byte hash.** Legends are keyed by `figs/<sha1(source bytes)[:16]>.jpg`. Re-exporting a plot
changes its key, so it re-enters `todo_legends.json` - correct behaviour, the old legend may no longer fit.

**Same plot twice.** Notebooks often re-display a saved PNG, giving two slightly different encodings of one figure.
`build_notes.py` removes near-duplicates within a run by a 24×24 average hash (≤ 20 differing bits).

**Shared notebooks mis-assign figures.** Several runs sharing one notebook without `(§a–b)` hints are matched to parts
by heading words; expect a few wrong. Legend agents catch them; record them in `fig_fixes.json`.

**Publishing limits.** One Artifact publish takes at most 255 files; publish the page with `root` = build folder and the
figure batches from `publish_batches.json`, one publish per batch, same file path.

**Sharing.** OneDrive/SharePoint links from an institution ask outside people to log in. Email the zip instead.

**Agents and scratch space.** Parallel agents writing helpers into one folder overwrote each other's merge scripts and
output files. One folder and one output file per agent.

**What the map exposed.** Writing plain-language notes and legends against the code found real problems (a leaked gene
selection, mislabelled plot panels, permutation counts different from the docs). Collect the agents' conflict reports
and offer the user a correction pass on the catalogue.
