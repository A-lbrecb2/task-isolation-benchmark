#!/usr/bin/env python3
"""Static context comparison: how many tokens of source code does the agent face?

    python3 kit/scripts/context_tokens.py --full full-repo --slices slices [--tasks-json kit/tasks.json]

Counts tokens (tiktoken o200k_base; other tokenizers differ by a few percent, the ratio is
what matters) for application code (src/app) and project configuration (top-level config
files plus src/*.ts, src/*.html) in

  * the full repository (Arm A), and
  * each task's slice (Arm B).

Lock files, documentation, assets and node_modules are excluded on both sides. The numbers
describe the OFFERED context, not what the agent actually reads. Use them on stage as the
"why"; the measured credits from VS Code are the "what".

Count exactly the files an agent listed under "Used N references":
    python3 context_tokens.py --files-from references.txt --repo full-repo
"""
import argparse
import json
import os

import tiktoken

TEXT_EXT = {".ts", ".html", ".scss", ".css", ".json", ".js", ".md"}
SKIP_DIRS = {".git", "node_modules", "dist", ".angular", "documentation", "e2e", "typings", ".github"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "karma.headless.js"}

enc = tiktoken.get_encoding("o200k_base")


def count_file(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return len(enc.encode(fh.read()))


def walk(root, predicate):
    total, n = 0, 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if os.path.splitext(f)[1] not in TEXT_EXT or f in SKIP_FILES:
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if predicate(rel):
                total += count_file(p)
                n += 1
    return total, n


def app_code(rel):
    return rel.startswith("src/app/")


def config(rel):
    top_level = "/" not in rel
    src_root = rel.startswith("src/") and rel.count("/") == 1
    env = rel.startswith("src/environments/")
    return top_level or src_root or env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", help="path to the full repository (Arm A)")
    ap.add_argument("--slices", help="folder that contains one slice per task (Arm B)")
    ap.add_argument("--tasks-json", default=os.path.join(os.path.dirname(__file__), "..", "tasks.json"))
    ap.add_argument("--files-from", help="text file with one repo-relative path per line")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    if args.files_from:
        total = 0
        with open(args.files_from, encoding="utf-8") as fh:
            for line in fh:
                rel = line.strip()
                if not rel:
                    continue
                t = count_file(os.path.join(args.repo, rel))
                total += t
                print(f"{t:>8}  {rel}")
        print(f"{total:>8}  TOTAL")
        return

    if not (args.full and args.slices):
        ap.error("--full and --slices are required unless --files-from is used")

    with open(args.tasks_json, encoding="utf-8") as fh:
        tasks = json.load(fh)["tasks"]

    f_app, f_app_n = walk(args.full, app_code)
    f_cfg, f_cfg_n = walk(args.full, config)

    print("Offered context in tokens (o200k_base)")
    print(f"  full repository: src/app {f_app:>7} tokens in {f_app_n:>2} files, config {f_cfg:>6} tokens in {f_cfg_n:>2} files, total {f_app + f_cfg}")
    print()
    print(f"  {'task':<5}{'slice':<20}{'src/app':>9}{'files':>7}{'config':>9}{'total':>9}{'full':>9}{'reduction':>11}")
    for t in tasks:
        sdir = os.path.join(args.slices, t["slice_dir"])
        s_app, s_app_n = walk(sdir, app_code)
        s_cfg, _ = walk(sdir, config)
        s_tot, f_tot = s_app + s_cfg, f_app + f_cfg
        print(f"  {t['id']:<5}{t['slice_dir']:<20}{s_app:>9}{s_app_n:>7}{s_cfg:>9}{s_tot:>9}{f_tot:>9}{1 - s_tot / f_tot:>10.0%}")
    print()
    print("Reduction = 1 - slice total / full total, application code plus configuration.")


if __name__ == "__main__":
    main()
