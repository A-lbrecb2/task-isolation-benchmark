#!/usr/bin/env python3
"""Runtime software bill of materials for one Angular project, and a diff between two.

    python3 kit/scripts/sbom.py generate <project> [--out sbom.cdx.json]
    python3 kit/scripts/sbom.py diff <baseline.json> <project-or-sbom.json>
    python3 kit/scripts/sbom.py compare full-repo slices/T1-table-list slices/T3-footer ...

`generate` walks the project's package.json `dependencies` (runtime only, no devDependencies)
through the installed node_modules the way Node resolves them, and writes a CycloneDX 1.5
JSON document: one component per resolved package version, with name, version, license
(from the package's own package.json) and purl. It does not need npm: `npm sbom` refuses the
origin repository because its lock file predates its package.json, and the workbenches ship
without lock files.

`diff` prints the components that were added or removed relative to a baseline. A non-empty
"added" list is a policy violation (check_policy.py uses it).

`compare` prints one row per project: direct runtime dependencies, resolved runtime
components, and the reduction against the first project. Used for the deck.

Direct dependencies are the honest number for "what the agent is allowed to import".
Resolved components are the honest number for "what ships".
"""
import argparse
import json
import os
import sys

CDX_VERSION = "1.5"


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def find_package(name, start_dir, root):
    """Resolve `name` the way Node does: nearest node_modules walking up from start_dir to root."""
    d = os.path.abspath(start_dir)
    root = os.path.abspath(root)
    while True:
        cand = os.path.join(d, "node_modules", *name.split("/"))
        if os.path.isfile(os.path.join(cand, "package.json")):
            return cand
        if d == root or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def license_of(pkg):
    lic = pkg.get("license")
    if isinstance(lic, dict):
        return lic.get("type", "")
    if isinstance(lic, str):
        return lic
    lics = pkg.get("licenses")
    if isinstance(lics, list) and lics:
        return " OR ".join(l.get("type", "") if isinstance(l, dict) else str(l) for l in lics)
    return ""


def generate(project):
    project = os.path.abspath(project)
    root_pkg = read_json(os.path.join(project, "package.json"))
    direct = sorted(root_pkg.get("dependencies", {}).keys())
    seen = {}      # (name, version) -> component
    missing = []
    stack = [(name, project) for name in direct]
    while stack:
        name, from_dir = stack.pop()
        loc = find_package(name, from_dir, project)
        if loc is None:
            missing.append(name)
            continue
        pkg = read_json(os.path.join(loc, "package.json"))
        key = (pkg.get("name", name), pkg.get("version", "?"))
        if key in seen:
            continue
        seen[key] = {
            "type": "library",
            "name": key[0],
            "version": key[1],
            "purl": f"pkg:npm/{key[0]}@{key[1]}",
            "licenses": [{"license": {"id": license_of(pkg)}}] if license_of(pkg) else [],
            "properties": [{"name": "benchmark:direct", "value": "true" if name in direct and from_dir == project else "false"}],
        }
        for dep in sorted(pkg.get("dependencies", {}).keys()):
            stack.append((dep, loc))
        # optionalDependencies are installed when possible; count them if present
        for dep in sorted(pkg.get("optionalDependencies", {}).keys()):
            if find_package(dep, loc, project):
                stack.append((dep, loc))
    components = [seen[k] for k in sorted(seen)]
    doc = {
        "bomFormat": "CycloneDX",
        "specVersion": CDX_VERSION,
        "version": 1,
        "metadata": {
            "component": {"type": "application", "name": root_pkg.get("name", os.path.basename(project)), "version": root_pkg.get("version", "0.0.0")},
            "properties": [
                {"name": "benchmark:direct_dependencies", "value": str(len(direct))},
                {"name": "benchmark:resolved_components", "value": str(len(components))},
                {"name": "benchmark:missing", "value": ",".join(sorted(set(missing)))},
            ],
        },
        "components": components,
    }
    return doc, direct, missing


def load_sbom_or_project(path):
    if os.path.isdir(path):
        return generate(path)[0]
    return read_json(path)


def purls(doc):
    """purl set of a CycloneDX document; npm writes %40 for scoped packages, we write @; strip qualifiers."""
    out = set()
    for c in doc.get("components", []):
        p = c.get("purl") or f"pkg:npm/{c.get('name')}@{c.get('version')}"
        out.add(p.replace("%40", "@").split("?")[0])
    return out


def cmd_generate(a):
    doc, direct, missing = generate(a.project)
    out = a.out or os.path.join(a.project, "sbom.cdx.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    print(f"wrote {out}: {len(direct)} direct runtime dependencies, {len(doc['components'])} resolved components"
          + (f", {len(set(missing))} not installed: {', '.join(sorted(set(missing)))}" if missing else ""))


def cmd_diff(a):
    base = read_json(a.baseline)
    cur = load_sbom_or_project(a.current)
    added = sorted(purls(cur) - purls(base))
    removed = sorted(purls(base) - purls(cur))
    print(f"baseline {len(purls(base))} components, current {len(purls(cur))} components")
    print("added  :", ", ".join(added) if added else "none")
    print("removed:", ", ".join(removed) if removed else "none")
    if a.json:
        print(json.dumps({"added": added, "removed": removed}))
    return 1 if added else 0


def cmd_compare(a):
    rows = []
    for p in a.projects:
        doc, direct, missing = generate(p)
        rows.append((p, len(direct), len(doc["components"]), len(set(missing))))
    ref = rows[0]
    print("| Project | Direct runtime deps | Resolved runtime components | Reduction vs first |")
    print("| --- | --- | --- | --- |")
    for p, d, c, m in rows:
        red = "-" if p == ref[0] else f"{(1 - c / ref[2]) * 100:.0f}%"
        note = f" ({m} not installed)" if m else ""
        print(f"| {p} | {d} | {c}{note} | {red} |")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("project"); g.add_argument("--out")
    d = sub.add_parser("diff"); d.add_argument("baseline"); d.add_argument("current"); d.add_argument("--json", action="store_true")
    c = sub.add_parser("compare"); c.add_argument("projects", nargs="+")
    a = ap.parse_args()
    if a.cmd == "generate":
        cmd_generate(a)
    elif a.cmd == "diff":
        sys.exit(cmd_diff(a))
    else:
        cmd_compare(a)


if __name__ == "__main__":
    main()
