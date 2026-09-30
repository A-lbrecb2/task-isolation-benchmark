#!/usr/bin/env python3
"""Generate guardrails for one arm of one task.

    python3 kit/scripts/make_guardrails.py --task T3 --arm B --target full-repo
    python3 kit/scripts/make_guardrails.py --task T3 --arm C --target slices/T3-footer
    python3 kit/scripts/make_guardrails.py --task T3 --remove --target full-repo

Writes two files into the target folder, both generated from kit/tasks.json so nobody
types scope rules by hand:

  .github/copilot-instructions.md   textual guardrail: task scope, allowed files, forbidden
                                    actions, how to verify. Copilot reads it automatically.
  .vscode/settings.json             technical guardrail (arm B only): files.exclude and
                                    search.exclude hide everything outside the allowed
                                    folders from Explorer, quick open and search.

Arm A gets nothing. Arm B (full repository plus guardrails) gets both files. Arm C
(isolation) gets the instructions file only; there is nothing left to hide.

Arm A, second stage: after the agent has finished the task prompt, the Verify block of the
instructions is sent as a second prompt, word for word (`--verify-prompt` prints it for the
task). Credits of that second turn are recorded as credits_verify. This shows what it costs to
add verification afterwards instead of giving the guardrails up front.

With --policy, a third layer is added to the instructions (arms B and C alike) and made
checkable by kit/scripts/check_policy.py:

  ## Policy                          no new dependencies, lock file untouched, allowed imports
                                    (from tasks.json), forbidden patterns, license allowlist
  .guardrails/sbom.baseline.json    runtime SBOM before the run (kit/scripts/sbom.py); the
                                    checker diffs the SBOM after the run against it

The policy text is identical in B and C; only the baseline SBOM differs, because the
codebases differ. That is the point.

Both files are untracked and are removed by `git clean -fd`, so a reset between runs
also removes the guardrails. score_diff.py ignores them.
"""
import argparse
import json
import os
import shutil
import sys

INSTRUCTIONS = """# Copilot instructions for this workspace

You are working on exactly one task in this repository. Stay inside its scope.

## Task
{title} ({task_id}): change `{component}` only.

## Files you may read and edit
{allowed}

## Rules
- Do not create, edit, rename or delete any file outside the list above.
- Do not read or search files outside `{scope_dir}` unless the compiler forces you to; if you must look elsewhere, do not change anything there.
- Do not change shared modules, routing, package.json, angular.json or global styles.
- Do not add dependencies.
- Keep existing CSS classes and the existing public API of the component unless the task says otherwise.

{verify}"""

VERIFY = """## Verify
- The code must compile: `npx ng build`.
- The existing spec in `{scope_dir}` must still pass: `npx ng test --watch=false --karma-config karma.headless.js`.
- When you are done, list the files you changed.
"""


POLICY = """
## Policy (checked by kit/scripts/check_policy.py after the run)
- Do not add, remove or upgrade dependencies. `package.json` and the lock file stay as they are; `.guardrails/sbom.baseline.json` is the runtime SBOM this run is measured against.
- Import only from these modules inside the files you edit:
{allowed_imports}
- Do not use `eval`, `Function(...)`, `innerHTML`, `document.write`, `http://` URLs, or hard-coded secrets and tokens.
- Do not introduce `any` in code you write; keep the existing TypeScript strictness.
- Every third-party package in the runtime tree stays under one of these licenses: {licenses}. Adding anything else is a violation even if the package is small.
- If a rule blocks the task, stop and say so instead of working around it.
"""

DEFAULT_LICENSES = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD"]
FORBIDDEN_PATTERNS = [r"\beval\s*\(", r"\bnew\s+Function\s*\(", r"\binnerHTML\b", r"document\.write\s*\(", r"http://", r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}"]


def load_task(tasks_json, task_id):
    with open(tasks_json, encoding="utf-8") as fh:
        tasks = {t["id"]: t for t in json.load(fh)["tasks"]}
    if task_id not in tasks:
        raise SystemExit(f"unknown task {task_id}; known: {', '.join(tasks)}")
    return tasks[task_id]


def write_instructions(target, task, policy=False):
    text = INSTRUCTIONS.format(
        title=task["title"], task_id=task["id"], component=task["component"],
        allowed="\n".join(f"- `{f}`" for f in task["allowed_files"]),
        scope_dir=task["slice_root"], verify=VERIFY.format(scope_dir=task["slice_root"]),
    )
    if task.get("dependencies_read_only"):
        text += "\n## Files you may read but must not change\n" + "\n".join(f"- `{f}`" for f in task["dependencies_read_only"]) + "\n"
    if policy:
        imports = task.get("allowed_imports") or ["@angular/core", "@angular/common"]
        text += POLICY.format(allowed_imports="\n".join(f"  - `{m}`" for m in imports),
                              licenses=", ".join(task.get("allowed_licenses", DEFAULT_LICENSES)))
    path = os.path.join(target, ".github", "copilot-instructions.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def write_workspace_settings(target, task):
    """Hide everything under src/app except the task folder, plus assets, docs, e2e."""
    scope = task["slice_root"]                      # e.g. src/app/components/footer
    parts = scope.split("/")
    exclude = {}
    # walk down the scope path and hide the siblings at every level
    for depth in range(len(parts)):
        parent = "/".join(parts[:depth]) if depth else ""
        keep = parts[depth]
        parent_abs = os.path.join(target, parent) if parent else target
        if not os.path.isdir(parent_abs):
            continue
        for entry in sorted(os.listdir(parent_abs)):
            if entry == keep or entry.startswith("."):
                continue
            rel = f"{parent}/{entry}" if parent else entry
            # keep project configuration visible at the root and in src/
            if parent == "" and entry in ("angular.json", "package.json", "tsconfig.json", "karma.conf.js", "karma.headless.js"):
                continue
            if parent == "src" and entry in ("tsconfig.app.json", "tsconfig.spec.json", "test.ts", "polyfills.ts", "main.ts", "environments"):
                continue
            exclude[rel] = True
    exclude.update({"node_modules": True, "dist": True, ".angular": True})
    path = os.path.join(target, ".vscode", "settings.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # VS Code writes its own keys into this file (e.g. chat.agentSkillsLocations) when the
    # folder is opened. Merge instead of overwrite, so neither side loses its entries.
    settings = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                settings = json.load(fh)
        except (OSError, ValueError):
            settings = {}
    settings["files.exclude"] = exclude
    settings["search.exclude"] = exclude
    settings["files.watcherExclude"] = {"**/node_modules/**": True}
    settings["// benchmark"] = f"generated by make_guardrails.py for {task['id']}; visibility guardrail for arm B"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)
        fh.write("\n")
    return path, len(exclude)


def write_sbom_baseline(target):
    """Runtime SBOM of the arm folder before the run, via kit/scripts/sbom.py."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(target, ".guardrails")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sbom.baseline.json")
    r = subprocess.run([sys.executable, os.path.join(here, "sbom.py"), "generate", target, "--out", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("sbom baseline failed:", r.stderr.strip() or r.stdout.strip())
        return None
    print(r.stdout.strip())
    return out


GUARDRAIL_KEYS = ("files.exclude", "search.exclude", "files.watcherExclude", "// benchmark")


def remove(target):
    removed = []
    p = os.path.join(target, ".github", "copilot-instructions.md")
    if os.path.exists(p):
        os.remove(p)
        removed.append(".github/copilot-instructions.md")
    p = os.path.join(target, ".vscode", "settings.json")
    if os.path.exists(p):
        # only strip our keys; keep whatever VS Code wrote
        try:
            with open(p, encoding="utf-8") as fh:
                settings = json.load(fh)
        except (OSError, ValueError):
            settings = None
        if settings is None or not any(k in settings for k in GUARDRAIL_KEYS):
            pass
        else:
            for k in GUARDRAIL_KEYS:
                settings.pop(k, None)
            if settings:
                with open(p, "w", encoding="utf-8") as fh:
                    json.dump(settings, fh, indent=2)
                    fh.write("\n")
                removed.append(".vscode/settings.json (guardrail keys)")
            else:
                os.remove(p)
                removed.append(".vscode/settings.json")
    p = os.path.join(target, ".guardrails")
    if os.path.isdir(p):
        shutil.rmtree(p)
        removed.append(".guardrails/")
    for d in (".github", ".vscode"):
        p = os.path.join(target, d)
        if os.path.isdir(p) and not os.listdir(p):
            shutil.rmtree(p)
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", choices=["A", "B", "C"], help="A: none, B: instructions + workspace restriction, C: instructions only")
    ap.add_argument("--target", default=".", help="folder the agent will open as workspace root")
    ap.add_argument("--tasks-json", default=os.path.join(os.path.dirname(__file__), "..", "tasks.json"))
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--policy", action="store_true", help="add the Policy section and write .guardrails/sbom.baseline.json (arms B and C)")
    ap.add_argument("--verify-prompt", action="store_true", help="print the Verify block for the task (arm A's second prompt) and exit")
    args = ap.parse_args()

    if args.verify_prompt:
        task = load_task(args.tasks_json, args.task)
        print(VERIFY.format(scope_dir=task["slice_root"]).strip())
        return

    if args.remove:
        print("removed:", ", ".join(remove(args.target)) or "nothing")
        return
    if not args.arm:
        ap.error("--arm is required unless --remove is used")
    task = load_task(args.tasks_json, args.task)
    remove(args.target)
    if args.arm == "A":
        print("arm A: no guardrails written")
        return
    p = write_instructions(args.target, task, policy=args.policy)
    print("wrote", p, "(with policy)" if args.policy else "")
    if args.arm == "B":
        p, n = write_workspace_settings(args.target, task)
        print(f"wrote {p} ({n} paths hidden)")
    if args.policy:
        write_sbom_baseline(args.target)


if __name__ == "__main__":
    main()
