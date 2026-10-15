# Import Impact

Before changing an unfamiliar Python module, find its explicit local importers,
their transitive importers, and affected `__main__` entry points. This tool reads
source through the existing sibling **Import Map** tool and never executes the
inspected project. Python 3.9+ and the standard library are sufficient, offline.
Keep both tool folders together when copying them to another workspace.

From the repository root, run this working example:

```sh
python3 -B line-3/tools/import-impact/impact.py line-3/tools/import-map/examples pkg.helper
```

Observed: three affected modules out of four. `main -> pkg.engine -> pkg.helper`
explains the entry point's dependency; `pkg.engine -> pkg.helper` explains the
direct importer. `pkg.helper` itself is included at distance zero. The report
also keeps the existing cycle and unresolved-import warning visible. Exit is 0
unless `--strict` is requested; that example returns 1 in strict mode.

For a real existing worker tool, this command reads its source only:

```sh
python3 -B line-3/tools/import-impact/impact.py line-1/tools/deadline-sentry deadline_sentry --json --strict
```

Observed: exit 0, two affected modules (`deadline_sentry`,
`test_deadline_sentry`), both entry points, one dependent, no issues, cycles or
recognized dynamic imports. [Retained report](observed-impact.json).
This describes dependency shape; the target's runtime tests were not executed.

Supply exact dotted module names as positional arguments, not filenames.
Multiple changed modules are allowed; duplicates are removed. The root is one
explicit import root, such as a project's `src/` directory, and must resolve
inside the current working directory. Run from your workspace root.
Unknown names, absent/outside roots and caught scan failures exit 2 with no
partial success report. `--json` returns deterministic JSON. `--strict` exits 1
when the underlying scan finds issues, cycles or recognized dynamic calls.
An impact finding alone is normal output, not an error.

Each affected module has a shortest `import_path`, ordered from importer to
changed module, plus its source path, entrypoint flag and edge distance.
Multi-source breadth-first traversal and sorted ties give reproducible paths.
Cycles terminate; a changed module is always its own zero-length seed even if
it also depends on another changed module. The JSON includes all scan issues,
cycle groups and recognized dynamic calls, including those outside the impact
set; text output gives their counts. Use JSON for their exact locations.

Verify from the repository root:

```sh
python3 -B -m unittest discover -s line-3/tools/import-impact -v
```

Tried locally: **8 tests passed**. They cover direction, shortest witnesses,
deterministic ties, multiple seeds, cycles, self-imports, duplicates, unknown
names, source encoding, parse/dynamic warnings, CLI statuses, a source execution
trap and a 1,500-module chain. Eighty deterministic random graphs are checked
against independently computed forward reachability and shortest distances.
The sibling mapper's **10 existing tests also passed**, unchanged.

Limits: this traces the mapper's explicit static local edges, not all Python
runtime dependencies. Implicit package-initializer execution, import side
effects, plugins, custom import hooks and dynamic imports can add dependencies
that are absent here. Attribute-versus-submodule ambiguity follows Import Map's
conservative resolution; conditional and function-local imports are included
without proving they run. A parse error or collision can hide useful edges.
Absence from the result never proves isolation. Only `__main__` guards identify
entry points; packaging scripts are not inferred. Whole-tree source scanning is
unbounded in total size, and emitting a full witness per module can use quadratic
space on long chains. No network, dependencies, wallet, coin or transaction is
needed by this tool.
