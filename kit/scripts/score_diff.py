#!/usr/bin/env python3
"""Diff precision scoring for the task-isolation benchmark.

Run inside the repository (full-repo or a slice) AFTER the agent has
finished and BEFORE the hidden spec file is copied in.

    python3 score_diff.py --task T1 --tasks-json ../tasks.json [--repo .] [--json]

It lists every file the agent created or modified (git status --porcelain), compares
the set with the task's allowed_files and prints:

    files_changed          number of files touched
    files_in_scope         touched files that belong to the task's allowed set
    diff_precision         files_in_scope / files_changed  (1.0 = nothing outside scope)
    lines_changed_total    added + deleted lines over all touched files (tracked files only)
    lines_out_of_scope     added + deleted lines in files outside the allowed set

Precision is file based on purpose: it is easy to explain on stage and independent of
code style. Line counts are reported as supporting evidence.
"""
import argparse
import json
import os
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def prefix(repo):
    """Path of `repo` inside its git work tree ('' when repo is the work tree root).
    Lets the benchmark live in a subfolder of a larger repository."""
    return git(repo, "rev-parse", "--show-prefix").strip()


def localize(path, pre):
    """Map a work-tree-relative path to a repo-dir-relative path, or None if outside."""
    if not pre:
        return path
    return path[len(pre):] if path.startswith(pre) else None


def changed_files(repo):
    pre = prefix(repo)
    files = set()
    for line in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        local = localize(path.strip('"'), pre)
        if local:
            files.add(local)
    return files


def numstat(repo):
    """added+deleted lines per tracked file (staged and unstaged)."""
    pre = prefix(repo)
    counts = {}
    for scope in (["--numstat"], ["--numstat", "--cached"]):
        for line in git(repo, "diff", *scope).splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            add, dele, path = parts
            if add == "-" or dele == "-":
                continue
            local = localize(path, pre)
            if local:
                counts[local] = counts.get(local, 0) + int(add) + int(dele)
    return counts


GUARDRAIL_FILES = (".github/copilot-instructions.md", ".vscode/settings.json")


def is_guardrail(path):
    """Files written by make_guardrails.py are part of the arm's setup, not of the agent's diff."""
    return path in GUARDRAIL_FILES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="task id, e.g. T1")
    ap.add_argument("--tasks-json", default=os.path.join(os.path.dirname(__file__), "..", "tasks.json"))
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true", help="print machine readable JSON only")
    args = ap.parse_args()

    with open(args.tasks_json, encoding="utf-8") as fh:
        tasks = {t["id"]: t for t in json.load(fh)["tasks"]}
    if args.task not in tasks:
        sys.exit(f"unknown task {args.task}; known: {', '.join(tasks)}")
    task = tasks[args.task]
    allowed = set(task["allowed_files"])
    spec_path = task["spec_target_path"]

    touched = {f for f in changed_files(args.repo) if f != spec_path and not is_guardrail(f)}
    in_scope = {f for f in touched if f in allowed}
    out_scope = touched - in_scope

    lines = numstat(args.repo)
    total_lines = sum(v for k, v in lines.items() if k != spec_path and not is_guardrail(k))
    out_lines = sum(v for k, v in lines.items() if k in out_scope)

    result = {
        "task": args.task,
        "files_changed": len(touched),
        "files_in_scope": len(in_scope),
        "diff_precision": round(len(in_scope) / len(touched), 3) if touched else 0.0,
        "lines_changed_total": total_lines,
        "lines_out_of_scope": out_lines,
        "touched_files": sorted(touched),
        "out_of_scope_files": sorted(out_scope),
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"Task {args.task}: {task['title']}")
    print(f"  files changed      : {result['files_changed']}")
    print(f"  files in scope     : {result['files_in_scope']}")
    print(f"  diff precision     : {result['diff_precision']:.2f}")
    print(f"  lines changed      : {total_lines} (out of scope: {out_lines})")
    if out_scope:
        print("  out of scope files :")
        for f in sorted(out_scope):
            print(f"    - {f}")
    if not touched:
        print("  WARNING: no changes detected. Did the agent write anything?")


if __name__ == "__main__":
    main()
