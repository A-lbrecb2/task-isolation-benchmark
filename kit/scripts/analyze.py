#!/usr/bin/env python3
"""Aggregate benchmark runs and draw the comparison chart.

    python3 analyze.py ../results/results.csv --out ../results/summary

Produces <out>.md (table for the wiki / Reddit post) and <out>.png (three panels:
credits, test pass rate, diff precision; one bar pair per task).

Definitions
  arms               A_full_repo, B_full_repo_guardrails, C_isolation (B_workbench / C_crodox map to C)
  credits            credits_turn (single prompt per run)
  test pass rate     tests_passed / tests_total
  diff precision     files_in_scope / files_changed (0 when nothing changed)
  precision index    mean of test pass rate and diff precision, the one number for the slide
  reduction          1 - mean(arm) / mean(A), per task and overall (overall = mean of task means,
                     so every task weighs the same)
"""
import argparse
import csv
import statistics as st
from collections import defaultdict

ARMS = ["A_full_repo", "B_full_repo_guardrails", "C_isolation"]
ARM_A, ARM_B, ARM_C = ARMS
LABEL = {ARM_A: "Full repo", ARM_B: "Full repo + guardrails", ARM_C: "Isolation + guardrails"}
# Palette: black / gray only, darkest = baseline.
COLOR = {ARM_A: "#1a1a1a", ARM_B: "#6e6e6e", ARM_C: "#b5b5b5"}
# Older result files may still use B_workbench for the isolation arm.
ARM_ALIASES = {"B_workbench": ARM_C, "C_crodox": ARM_C}


def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r.get("task"):
                continue
            tests_total = float(r["tests_total"] or 0)
            files_changed = float(r["files_changed"] or 0)
            rows.append({
                "task": r["task"].strip(),
                "arm": ARM_ALIASES.get(r["arm"].strip(), r["arm"].strip()),
                "credits": float(r["credits_turn"] or 0),
                "tokens": float(r["context_tokens_session"] or 0),
                "pass_rate": float(r["tests_passed"] or 0) / tests_total if tests_total else 0.0,
                "diff_prec": float(r["files_in_scope"] or 0) / files_changed if files_changed else 0.0,
                "build_ok": float(r["build_ok"] or 0),
            })
    return rows


def aggregate(rows):
    cell = defaultdict(list)
    for r in rows:
        cell[(r["task"], r["arm"])].append(r)
    tasks = sorted({r["task"] for r in rows})
    agg = {}
    for t in tasks:
        for arm in ARMS:
            rs = cell.get((t, arm), [])
            if not rs:
                continue
            agg[(t, arm)] = {
                "n": len(rs),
                "credits": st.mean(r["credits"] for r in rs),
                "credits_median": st.median(r["credits"] for r in rs),
                "tokens": st.mean(r["tokens"] for r in rs),
                "pass_rate": st.mean(r["pass_rate"] for r in rs),
                "diff_prec": st.mean(r["diff_prec"] for r in rs),
                "build_ok": st.mean(r["build_ok"] for r in rs),
            }
            agg[(t, arm)]["precision_index"] = (agg[(t, arm)]["pass_rate"] + agg[(t, arm)]["diff_prec"]) / 2
    return tasks, agg


def pct(x):
    return f"{x * 100:.0f}%"


def write_markdown(tasks, agg, path):
    lines = ["| Task | Arm | Runs | Credits | Credit reduction vs A | Tokens | Token reduction vs A | Tests | Diff prec. | Precision index |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    overall = {arm: {"red_c": [], "red_t": [], "pi": []} for arm in ARMS}
    for t in tasks:
        a = agg.get((t, ARM_A))
        for arm in ARMS:
            x = agg.get((t, arm))
            if not x:
                continue
            rc = 1 - x["credits"] / a["credits"] if a and a["credits"] else 0
            rt = 1 - x["tokens"] / a["tokens"] if a and a["tokens"] else 0
            overall[arm]["red_c"].append(rc); overall[arm]["red_t"].append(rt); overall[arm]["pi"].append(x["precision_index"])
            lines.append(f"| {t} | {LABEL[arm]} | {x['n']} | {x['credits']:.2f} | {pct(rc) if arm != ARM_A else '-'} | "
                         f"{x['tokens']:.0f} | {pct(rt) if arm != ARM_A else '-'} | {pct(x['pass_rate'])} | {pct(x['diff_prec'])} | {pct(x['precision_index'])} |")
    lines.append("")
    for arm in ARMS:
        o = overall[arm]
        if not o["pi"]:
            continue
        if arm == ARM_A:
            lines.append(f"Overall {LABEL[arm]}: precision index {pct(st.mean(o['pi']))}.")
        else:
            lines.append(f"Overall {LABEL[arm]} (mean of task means): credit reduction {pct(st.mean(o['red_c']))}, "
                         f"token reduction {pct(st.mean(o['red_t']))}, precision index {pct(st.mean(o['pi']))}.")
    b, c = overall[ARM_B], overall[ARM_C]
    if b["pi"] and c["pi"]:
        # direct C-vs-B reduction per task (same instructions, only the codebase differs)
        red_cb_c, red_cb_t = [], []
        for t in tasks:
            xb, xc = agg.get((t, ARM_B)), agg.get((t, ARM_C))
            if xb and xc:
                if xb["credits"]:
                    red_cb_c.append(1 - xc["credits"] / xb["credits"])
                if xb["tokens"]:
                    red_cb_t.append(1 - xc["tokens"] / xb["tokens"])
        if red_cb_c:
            lines.append(f"Isolation vs guardrails alone (C relative to B, mean of task means): credits {pct(st.mean(red_cb_c))} less, "
                         f"tokens {pct(st.mean(red_cb_t))} less, precision index {pct(st.mean(c['pi']) - st.mean(b['pi']))} points difference.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def draw(tasks, agg, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [("credits", "Credits per prompt", False), ("pass_rate", "Tests passed", True), ("diff_prec", "Diff precision", True)]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), dpi=150)
    fig.patch.set_facecolor("white")
    x = range(len(tasks))
    present = [arm for arm in ARMS if any((t, arm) in agg for t in tasks)]
    w = 0.88 / max(len(present), 1) - 0.02
    for ax, (key, title, is_pct) in zip(axes, panels):
        for i, arm in enumerate(present):
            vals = [agg.get((t, arm), {}).get(key, 0) for t in tasks]
            offset = (i - (len(present) - 1) / 2) * (w + 0.02)
            bars = ax.bar([xi + offset for xi in x], vals, width=w, color=COLOR[arm], label=LABEL[arm], linewidth=0)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), pct(v) if is_pct else f"{v:.2f}",
                        ha="center", va="bottom", fontsize=7, color="#333333")
        ax.set_title(title, fontsize=11, loc="left", color="#111111")
        ax.set_xticks(list(x)); ax.set_xticklabels(tasks, fontsize=9)
        ax.tick_params(axis="y", labelsize=8, colors="#555555")
        if is_pct:
            ax.set_ylim(0, 1.12)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        else:
            ax.set_ylim(0, max([agg[k]["credits"] for k in agg] + [1]) * 1.18)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#cccccc")
        ax.yaxis.grid(True, color="#e6e6e6", linewidth=0.8); ax.set_axisbelow(True)
    axes[0].legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 1.22), ncol=3)
    fig.suptitle("Full repository vs. guardrails vs. isolation, GitHub Copilot agent mode", x=0.01, ha="left", fontsize=12, color="#111111", y=1.02)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    print(f"chart written to {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="summary")
    args = ap.parse_args()
    rows = load(args.csv)
    if not rows:
        raise SystemExit("no rows found")
    tasks, agg = aggregate(rows)
    write_markdown(tasks, agg, args.out + ".md")
    draw(tasks, agg, args.out + ".png")


if __name__ == "__main__":
    main()
