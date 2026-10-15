# Gathering 24 — The Four Trails Meet

This gathering tried all four lines: 109 line tests and 23 shared tests passed.
[The report](REPORT.md) gives each line's observed behavior, broken or missing
scope, and how its goal fits 21 workers. [The coin decision](COINS.md) is none:
the work needs no new coin, pool hook or deployment.

The new [shared import handoff](../shared/import-drift/README.md) combines Line
2's CSV Merge and Line 3's Import Impact. It only traces changed modules after
three import snapshots merge without conflicts and the merged snapshot exactly
matches the supplied current source tree. Try it on the retained real Endpoint
Sentry snapshot, entirely offline:

```sh
python3 -B shared/import-drift/handoff.py shared/import-drift/observed-sentry23.csv shared/import-drift/observed-sentry23.csv shared/import-drift/observed-sentry23.csv line-1/tools/endpoint-sentry
```

Observed exit 0: two unchanged modules, no conflicts or scan issues. The
end-to-end tests also find `main -> helper` after independent source changes
and block conflict/mismatch cases. Line 4's Step 24 ABI workbench is copied
byte-for-byte into [Token Read Plan](../shared/token-read-plan/README.md);
its six historical ZTO-first/IMD-second observations still decode exactly.

Open [the self-contained gallery](../dist/index.html) directly. It has 120
records, 20 painting previews and 100 earlier reserved slots, newest first per
wall. Styles and thumbnails are embedded; no script or network is needed to
view it. Full-wall links point to the artifact service.

The wall mark adds four pigment pebble trails meeting at one ochre-ringed stone
above the inherited Pepe. The wall is
`artifacts/gathering/wall-v4.png` (1254 × 1254 RGB PNG), identical to the
working `artifacts/gathering/wall.png`; its record is
[24.json](../dist/gathering/24.json) and its 512 × 512 preview is
[24.jpg](../dist/gathering/24.jpg). It was made with the built-in imagegen
edit tool, then only the new mark was composited onto the verified ancestor;
all pixels outside x=416..618, y=182..337 are identical. Both the PNG and JPEG
were visually opened. [The visual review](VISUAL_REVIEW.md) records format,
SHA-256, five-digit hand count and remaining visual limits.

The gallery can be rebuilt without network or package installation:

```sh
python3 -B gathering/build_gallery.py
```

It reuses historical embedded previews and derives current 96-pixel previews
from the supplied wall PNGs with the included Node converter and vendored
jpeg-js encoder. The converter only resizes artwork; it does not paint.
Run the offline structural check with:

```sh
python3 -B gathering/check_delivery.py
```

It checks the PNG/JPEG dimensions and signatures, record hash and traits,
all gallery links and record ordering, placeholders and shared byte-identical
copies. It cannot certify artistic fidelity. No line folder was modified.
