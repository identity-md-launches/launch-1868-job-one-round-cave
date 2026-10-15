#!/usr/bin/env python3
"""Explain static reverse-import impact without executing inspected code."""

import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import sys


def load_mapper():
    # Load only our delivered sibling tool, never a module from the target tree.
    path = Path(__file__).resolve().parent / "import_map.py"
    spec = importlib.util.spec_from_file_location("pepeolithic_import_mapper", path)
    mapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapper)
    return mapper


def explain(report, changed):
    """One shortest importer-to-seed path per reachable module, including seeds.

    Sorted multi-source BFS makes equal-length choices deterministic. Iterative
    traversal terminates on cycles and does not depend on Python stack depth.
    """
    records = {item["module"]: item for item in report["modules"]}
    seeds = sorted(set(changed))
    if not seeds:
        raise ValueError("at least one changed module is required")
    unknown = sorted(set(seeds) - records.keys())
    if unknown:
        raise ValueError("unknown changed module(s): " + ", ".join(unknown))
    reverse = {name: set() for name in records}
    for edge in report["edges"]:
        reverse[edge["to"]].add(edge["from"])
    toward_seed = {name: None for name in seeds}
    distance = {name: 0 for name in seeds}
    pending = deque(seeds)
    while pending:
        target = pending.popleft()
        for importer in sorted(reverse[target]):
            if importer not in toward_seed:
                toward_seed[importer] = target
                distance[importer] = distance[target] + 1
                pending.append(importer)
    affected = []
    for name in sorted(toward_seed):
        path = [name]
        while toward_seed[path[-1]] is not None:
            path.append(toward_seed[path[-1]])
        item = records[name]
        affected.append({"module": name, "path": item["path"],
                         "entrypoint": item["entrypoint"],
                         "distance": distance[name], "import_path": path})
    dynamic = [{"module": item["module"], "path": item["path"], "line": line}
               for item in report["modules"]
               for line in item["dynamic_import_lines"]]
    return {"changed": seeds, "affected": affected,
            "issues": report["issues"], "cycles": report["cycles"],
            "dynamic_imports": dynamic,
            "summary": {"module_count": len(records),
                        "affected_count": len(affected),
                        "dependent_count": len(affected) - len(seeds),
                        "affected_entrypoints": [item["module"] for item in affected
                                                 if item["entrypoint"]]},
            "scope": "Static explicit local import edges only; absence is not proof of isolation."}


def format_text(result):
    summary = result["summary"]
    lines = ["Changed: " + ", ".join(result["changed"]),
             f"Affected: {summary['affected_count']} of {summary['module_count']} modules "
             f"({summary['dependent_count']} dependents plus changed modules)"]
    for item in result["affected"]:
        suffix = " [entry point]" if item["entrypoint"] else ""
        lines.append(" -> ".join(item["import_path"]) + suffix)
    lines.append(f"Scan warnings: {len(result['issues'])} issues, "
                 f"{len(result['cycles'])} cycle groups, "
                 f"{len(result['dynamic_imports'])} dynamic import calls")
    lines.append(result["scope"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="explicit Python import root under the current workspace")
    parser.add_argument("changed", nargs="+", help="exact dotted module names, including package names")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON with scan warnings")
    parser.add_argument("--strict", action="store_true", help="exit 1 for scan issues, cycles or dynamic imports")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if not root.is_relative_to(Path.cwd().resolve()) or not root.is_dir():
            raise ValueError("root must be an existing directory inside the current workspace")
        report = load_mapper().inspect(root)
        result = explain(report, args.changed)
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        print("import-impact: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_text(result))
    return int(args.strict and bool(result["issues"] or result["cycles"] or result["dynamic_imports"]))


if __name__ == "__main__":
    sys.exit(main())
