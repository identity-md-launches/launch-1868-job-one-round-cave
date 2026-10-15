# Step 24 — The Returning Trail

Added [Import Impact](tools/import-impact/README.md), a Python standard-library
tool for finding explicit reverse-import dependencies of changed modules. Each
result includes a shortest importer-to-change path, source path, distance, and
entrypoint flag. Multiple seeds, cycles and deterministic tie choices are
supported. Scan issues and recognized dynamic calls remain visible. The goal,
mapper implementation, existing tests and older records are unchanged.

## Commands and observed results

- `python3 -B -m unittest discover -s line-3/tools/import-impact -v`: **8 passed**,
  zero failures. Includes 80 random-graph comparisons against independent forward
  reachability, shortest witness validity and a 1,500-module chain.
- `python3 -B -m unittest discover -s line-3/tools/import-map -v`: **10 passed**,
  zero failures. Both suites were rerun after final tool documentation.
- `python3 -B line-3/tools/import-impact/impact.py line-3/tools/import-map/examples pkg.helper`:
  exit 0; three affected modules, one affected entry point, one issue and one
  cycle group, with `main -> pkg.engine -> pkg.helper` as the longest witness.
- `python3 -B line-3/tools/import-impact/impact.py line-1/tools/deadline-sentry deadline_sentry --json --strict`:
  exit 0; two affected modules and entry points, one dependent, no warnings.
  [Observed JSON](tools/import-impact/observed-impact.json). Inspected code was
  not executed; this does not certify the target's runtime behavior.
- Scratch artifact finalization: `node test/scratch/line3-step24/finalize.js`
  could not run because Node was absent (exit 127). No installation was made.
  A standard-library Python finalizer replaced it. Its first JPEG-size check
  failed with a custom Huffman table; using the workspace's standard JPEG
  luminance table values repaired the size. Final
  `python3 -B test/scratch/line3-step24/finalize.py` exited 0 and round-tripped
  the full PNG pixels exactly. These were processing failures, not failed tool
  behavior tests. Scratch code is not part of the deliverable.

The tool works offline with its existing sibling Import Map. It reports explicit
static edges only; implicit package-initializer dependencies, side effects and
runtime import hooks can be absent. A missing impact result never establishes
isolation. Whole-tree scanning remains unbounded, and explicit witness output
can occupy quadratic space on a long chain. No financial mechanism, coin,
wallet, chain state, signing or transaction is involved.

## Image and visual review

- Required output: `artifacts/line-3/wall-v4.png`, **1254 × 1254**, 8-bit RGB PNG,
  3,936,540 bytes. `artifacts/line-3/wall.png` is byte-identical.
- SHA-256: `f745d84ca9484eb9d228d1a1c152f828a4ac18882616686a5809499444cc2493`.
- New record: `dist/line-3/24.json`, the specified three fields and six traits.
  Number 24 is one more than the 23 inherited JSON records.
- Required preview: `dist/line-3/24.jpg`, baseline color JPEG, **512 × 512**,
  **89,842 bytes**. This explicitly required preview beside the record is the
  exception to the general rule against pictures outside artifacts.
- Missing ancestor recovered from record 23's public image URL with a dedicated
  User-Agent. SHA-256 matched
  `5a635d0b345691dd56be3f2ffa17a2ea6d0f0bc86664c33b7c45b4096f58d43e`.
- Built-in imagegen created the addition: an ochre seed with charcoal branches
  reaching two chalk stones, symbolizing tracing impact from a changed module.
  The generator placed it on the unused lower stone ledge. Finalization kept
  just x=645..814, y=1090..1189, with a ten-pixel boundary blend. **16,169 pixels
  changed inside; zero pixels changed outside**. All ancestor figures and marks,
  rock outside the patch, cracks, framing and torchlight are pixel-identical.
- Explicit review step: opened the final full PNG and the decoded JPEG with
  `view_image`, after output encoding. Pepe's wide mouth and heavy-lidded eyes
  remain. Both inherited hands have **five digits each**; no hands or handprints
  were added. The new mark uses earth pigments and irregular worn strokes.
  No letters, numbers, logos, signatures, borders or prohibited symbols observed.
- **Unmet visual requirements observed: none.** The insertion's stone texture can
  differ within its patch. JPEG compression and nearest-neighbor downsampling
  make the preview coarser than the reference PNG. Local review is not
  independent certification. Machine-readable facts: [checks](STEP-24-CHECKS.json).

## Final prompt supplied to the built-in image edit tool

> Use case: precise-object-edit. Edit this inherited prehistoric cave painting by adding just one small pigment mark on unused stone at lower center, bounded by x=580..755 y=925..1035 in this 1254 square image. The new mark symbolizes tracing dependency impact backward: one small red ochre seed dot at right, two short handmade charcoal trails branching toward two small chalk dots at left, a tiny yellow ochre fleck alongside the seed. Uneven, worn earth pigment with exposed stone showing through. No arrows, no writing, no letters or numbers. Preserve the entire existing image exactly: same square dimensions, rock texture, cracks, torchlight, framing, frog Pepe with wide mouth heavy-lidded eyes and both five-digit hands, all old trails and dots. Do not repaint, move, erase or redraw any existing marks. No new figures, hands, handprints, borders, logos or symbols. Add only this little branching mark in the specified unused lower-center stone patch.

The generator's actual placement differed from the prompt; its final patch
coordinates above describe the delivered result. Artistic content came from the
image tool; finalization confined it to unused stone to preserve the ancestors.
