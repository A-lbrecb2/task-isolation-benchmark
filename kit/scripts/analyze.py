#!/usr/bin/env python3
"""Aggregate benchmark runs and draw the comparison chart.

    python3 analyze.py ../results/results.csv --out ../results/summary

Produces <out>.md (table for the wiki / Reddit post) and <out>.png (three panels:
credits, test pass rate, diff precision; one bar pair per task).

Definitions
  credits            credits_turn (single prompt per run)
  test pass rate     tests_passed / tests_total
  diff precision     files_in_scope / files_changed (0 when nothing changed)
  precision index    mean of test pass rate and diff precision, the one number for the slide
  reduction          1 - mean(B) / mean(A), per task and overall (overall = mean of task means,
                     so every task weighs the same)
"""
import argparse
import csv
import statistics as st
from collections import defaultdict

ARM_A, ARM_B = "A_full_repo", "B_workbench"
LABEL = {ARM_A: "Full repo", ARM_B: "Isolated slice"}
# Palette: black / gray only.
COLOR = {ARM_A: "#1a1a1a", ARM_B: "#9a9a9a"}


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
                "arm": r["arm"].strip(),
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
        for arm in (ARM_A, ARM_B):
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
    lines = ["| Task | Runs A/B | Credits A | Credits B | Credit reduction | Tokens A | Tokens B | Token reduction | Tests A | Tests B | Diff prec. A | Diff prec. B | Precision index A | Precision index B |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    red_c, red_t, pi_a, pi_b = [], [], [], []
    for t in tasks:
        a, b = agg.get((t, ARM_A)), agg.get((t, ARM_B))
        if not (a and b):
            continue
        rc = 1 - b["credits"] / a["credits"] if a["credits"] else 0
        rt = 1 - b["tokens"] / a["tokens"] if a["tokens"] else 0
        red_c.append(rc); red_t.append(rt); pi_a.append(a["precision_index"]); pi_b.append(b["precision_index"])
        lines.append(f"| {t} | {a['n']}/{b['n']} | {a['credits']:.2f} | {b['credits']:.2f} | {pct(rc)} | "
                     f"{a['tokens']:.0f} | {b['tokens']:.0f} | {pct(rt)} | {pct(a['pass_rate'])} | {pct(b['pass_rate'])} | "
                     f"{pct(a['diff_prec'])} | {pct(b['diff_prec'])} | {pct(a['precision_index'])} | {pct(b['precision_index'])} |")
    if red_c:
        lines += ["",
                  f"Overall (mean of task means): credit reduction {pct(st.mean(red_c))}, "
                  f"token reduction {pct(st.mean(red_t))}, precision index {pct(st.mean(pi_a))} (full repo) "
                  f"vs {pct(st.mean(pi_b))} (workbench), difference {pct(st.mean(pi_b) - st.mean(pi_a))} points."]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def draw(tasks, agg, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [("credits", "Credits per prompt", False), ("pass_rate", "Tests passed", True), ("diff_prec", "Diff precision", True)]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)
    fig.patch.set_facecolor("white")
    x = range(len(tasks))
    w = 0.36
    for ax, (key, title, is_pct) in zip(axes, panels):
        for i, arm in enumerate((ARM_A, ARM_B)):
            vals = [agg.get((t, arm), {}).get(key, 0) for t in tasks]
            bars = ax.bar([xi + (i - 0.5) * (w + 0.02) for xi in x], vals, width=w, color=COLOR[arm], label=LABEL[arm], linewidth=0)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), pct(v) if is_pct else f"{v:.2f}",
                        ha="center", va="bottom", fontsize=8, color="#333333")
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
    axes[0].legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 1.22), ncol=2)
    fig.suptitle("Full repository vs. isolated slice, GitHub Copilot agent mode", x=0.01, ha="left", fontsize=12, color="#111111", y=1.02)
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
