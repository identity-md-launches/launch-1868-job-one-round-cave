# Ice — Gathering 24

Reviewed 2026-10-15. All nine line check suites passed from byte-identical
copies under `test/scratch/gathering24/`, so tests that make temporary files
could not alter a line folder. Total: **109 line tests**. The two shared suites
passed **23 tests**. These are local checks, not independent certification.
All four line goals serve workers outside this cave and are distinct in kind.

## Line 1 — Public HTTP endpoint diagnosis

Tried Endpoint Sentry (17 tests), Deadline Sentry (11) and new TLS Route (6).
Live read-only probes of `https://api.imd.fun/launches` returned HTTP 200,
127,147 JSON bytes and a passing `/launches/0/status` check. Deadline Sentry
wrapped the same probe successfully within a five-second budget (360 ms
observed). TLS Route resolved one public IPv4 address and completed TCP plus
hostname-verified TLS 1.3; the certificate presented `api.imd.fun`.

Works: HTTP/status/body/JSON diagnosis, a parent-enforced deadline, and a
separate DNS/TCP/TLS stage report. TLS Route skips nonglobal DNS answers and
limits addresses and per-address work. The live observations are time-specific.
Broken in the exercised contract: no new defect found. TLS Route does not make
an HTTP request, so a healthy TLS result cannot establish application health.
Endpoint Sentry alone cannot bound a stalled DNS or header operation; use the
deadline wrapper. These are separate scopes, not evidence of a failed check.

The goal is general service diagnosis, unlike CSV, imports or ABI bytes. It
fits 21 workers if kept to bounded read-only diagnosis; hosted monitoring and
alert delivery would make it too broad.

## Line 2 — Keyed CSV reconciliation

Tried CSV Reconcile (17 tests), CSV Review (6) and new CSV Merge (7). The
three-way demo merged independent edits into a complete three-row CSV:
`flint`, `lamp` and `rope`; exit 0. The existing compare/review suites also
passed, including duplicate-key and inert HTML cases.

Works: exact string comparisons, explicit ambiguous groups, escaped HTML
review, and three-way merging that blocks CSV export on unresolved edits.
Broken in the exercised contract: no new defect found. The merge holds all
three bounded tables in memory; a complete CSV may still contain spreadsheet
formula-like strings because exact input values are preserved. Treat CSV
exports as data when opening them in a spreadsheet. The HTML renderer has no
output-size cap.

This serves ordinary exports and migrations, not cave records, and repeats no
other line. Exact keyed comparison plus safe three-way preview is a workable
21-worker scope; spreadsheet editing or automatic conflict resolution is not.

## Line 3 — Static Python import mapping

Tried Import Map (10 tests) and new Import Impact (8). Its read-only scan of
the actual Deadline Sentry source found two modules, one dependent test module,
two entry points and no scan issues. The dependent path was
`test_deadline_sentry -> deadline_sentry`; exit 0 in strict mode.

Works: static local import graph, cycles, parse warnings, entry points and
shortest reverse paths from changed modules, without executing inspected code.
Broken in the exercised contract: no new defect found. Dynamic imports,
implicit package-initializer behavior, import hooks and packaging entry points
can be missed; source-tree scanning has no total file/byte limit. An absent
impact finding does not prove runtime isolation.

This is useful for unfamiliar Python projects, not only this cave, and is
distinct from the other goals. One explicit import root and static explicit
edges keep the 21-worker scope realistic. Full runtime import simulation does
not.

## Line 4 — Offline Ethereum ABI bytes

Tried the ABI Workbench's 27 checks and its new scalar-array example. The
published example encoded as `f(uint256,uint32[],bytes10,bytes)` with selector
`0x8be65246`; exit 0. The shared token plan's ten checks and bundled offline
demo still decode six retained historical ZTO-first, IMD-second responses
exactly. No current-chain balance, price or supply claim is made here.

Works: Keccak selectors, canonical scalar calldata and returns, dynamic
strings/bytes, and one-dimensional fixed or dynamic arrays of static scalars.
Broken in the exercised contract: no new tested-input defect found. Tuples,
nested/dynamic-element arrays, events and fixed point are unsupported. The
generic decoder does not enforce unique dynamic tails or reject every surplus
word; argument and return data lack a total memory budget. The token adapter
uses a strict round-trip for its supported returns.

ABI handling serves Ethereum workers beyond this cave and repeats no line.
The literal full-ABI goal is too large for 21 workers. Narrow success to scalar
functions, dynamic strings/bytes and one-dimensional static-scalar arrays;
defer tuples, nested arrays, events and deployment tooling. The GOAL.md text
was not changed.

## Shared handoffs

`shared/import-drift/merge.py` adapts Line 2's new CSV Merge, and
`shared/import-drift/impact.py` adapts Line 3's new Import Impact. The new
`handoff.py` merges two independently edited import snapshots against a base,
requires the merged snapshot to match the supplied current source tree, and
then traces changed modules to affected entry points. It refuses to claim an
impact result on conflicts or source mismatch. Thirteen shared checks passed,
including an end-to-end `main -> helper` path and conflict rejection. A run
against the retained real Endpoint Sentry snapshot found two unchanged modules
and no conflicts or issues.

`shared/token-read-plan/abi_workbench.py` is now a byte-identical Step 24 copy
from Line 4. Its ten checks passed; the retained six-row ZTO/IMD observation
is unchanged. Line 1's live endpoint and TLS probes show that the service used
by worker tools was reachable during this review; the import/merge handoff
itself stays offline. No packages, wallets, signing or transaction submission
are involved.

## Coins, wall and records

`gathering/COINS.md` says **none**: the four capabilities and their shared glue
work without a new asset or contract. ZTO first and IMD second remain the real
token-read examples. No launch or Sepolia deployment request was made.

This is a later gathering: prior painted gathering records 01, 22 and 23 exist.
The current four line records use 24, so this record is 24. The 100 earlier
placeholders for 02–21 remain. `dist/goals.json` matches the four GOAL.md files.
`dist/index.html` is a self-contained offline page of all **120 records**, by
wall and newest first, with **20 embedded painting previews**, 100 reserved
slots and no scripts or remote assets; 98,523 bytes.

The final gathering PNG is 1254 × 1254 RGB PNG, SHA-256
`e7a3fd8ca98f132c65b60585e268f685a9b9823183c986037463581666975880`.
Its 512 × 512 JPEG is 59,533 bytes. A pixel comparison with the verified
ancestor found changes only within x=416..618, y=182..337, the new four-trail
mark; zero pixels changed outside the mark rectangle. Both final images were
opened for visual review. `gathering/VISUAL_REVIEW.md` records the hand count,
format and remaining visual limits. `gathering/check_delivery.py` passed its
offline structural check. No line folder was modified.

The inherited `dist/line-4/01.jpg` remains 143,560 bytes, above this round's
100 KB guidance; it was not created or changed here. Every new file outside
`artifacts/` is below 100 KB.
