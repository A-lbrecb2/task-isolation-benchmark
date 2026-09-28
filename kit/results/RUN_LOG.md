# Run log

One row per run, in the order they happened. Runs that do not count stay in this log with
the reason; they are not copied to results.csv. This is where "the first B run had no
files.exclude" belongs, and where the Copilot numbers go before they are typed into the CSV.

| # | Date | Task | Arm | Valid | Model | Steps | Duration | Credits | Session tokens | References | Files changed / in scope | Tests passed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | T3 | A | no | Claude Sonnet, High 1M | 3 | 1m04s | | | | | | first round; .vscode present in full-repo, superseded by run 4 (not read out) |
| 2 | 2026-09-23 | T3 | B | no | Claude Sonnet, High 1M | | | | | | | | first round; nested full-repo/ folder inside armB-full-repo (Copy-Item into existing dir) |
| 3 | 2026-09-23 | T3 | C | no | Claude Sonnet, High 1M | 12 | 1m31s | | | | 2 / 2 | | first round; stray footer.bench.spec.ts with "404: Not Found" in workspace; agent cited guardrail, touched only footer.component.ts/.html |
| 4 | 2026-09-23 | T3 | A | yes | Claude Sonnet 5, High 1M | 3 | 22s | 8.6 | 36.8K | | 2 / 2 | 3/3, build OK | second round, C:\Crodox; no guardrails; MCP disabled; agent did not build or test |
| 5 | 2026-09-23 | T3 | B | no | Claude Sonnet, High 1M | 4 | 23s | | | | | | second round; instructions only, files.exclude missing (VS Code rewrote .vscode/settings.json). Interesting as "rules without visibility boundary" |
| 6 | 2026-09-23 | T3 | C | yes | Claude Sonnet 5, High 1M | | | 10.5 | 37.3K | | 2 / 2 | 3/3, build OK | second round; Crodox workbench t3-footer-crodox, guardrailScope patch; MCP disabled; agent ran build + test (2 specs, green) |
| 7 | 2026-09-23 | T3 | B | yes | Claude Sonnet 5, High 1M | 16 | 3m44s | 33.0 | 57.1K | | 2 / 2 | 3/3, build OK | second round; instructions + files.exclude (verified after run, VS Code only appended chat.agentSkillsLocations); MCP disabled; agent ran full suite (3 upstream failures) and investigated them |
| 8 | 2026-09-24 | T1 | A | yes | Claude Sonnet 5, High 1M | 14 | 54s | 21.1 | 49.8K | | 2 / 2 | 4/4, build OK | no guardrails; MCP disabled; agent changed .ts + .html, used currency pipe, did not run tests |
| 9 | 2026-09-24 | T1 | B | yes | Claude Sonnet 5, High 1M | 16 | 3m38s | 40.1 | 61.6K | | 4 / 4 | 4/4, build OK | instructions + files.exclude (T1); MCP disabled; agent created employee.ts, edited .ts/.html/.spec.ts (CommonModule import), ran full suite |
| 10 | 2026-09-24 | T1 | C | yes | Claude Sonnet 5, High 1M | 18 | 1m59s | 19.4 | 43.2K | | 2 / 2 | 4/4, build OK | Crodox workbench t1-table-list-crodox; MCP disabled; agent changed .ts + .html, ran tests (2 specs, green) |
| 11 | 2026-09-24 | T5 | B | no | Claude Sonnet 5, High 1M | | | | | | 0 / 0 | | armB still carried the T1 guardrails (make_guardrails --task T5 not yet run); agent refused: "restricts this session to TableListComponent files only", made no edits. Evidence that the instructions file is read and obeyed |
| 12 | 2026-09-24 | T5 | A | yes | Claude Sonnet 5, High 1M | 4 | 35s | 15.5 | 47.6K | | 1 / 1 | 3/3, build OK | no guardrails; MCP disabled; agent changed dashboard.component.ts only (per its summary), did not run tests |
| 13 | 2026-09-24 | T5 | B | yes | Claude Sonnet 5, High 1M | 21 | 2m09s | 35.2 | 64.4K | | 1 / 1 | 3/3, build OK | instructions + files.exclude (T5, commit c91b7c3); MCP disabled; agent changed dashboard.component.ts, ran build + full suite, then ~8 steps investigating the 3 upstream failures (searched terminal log, re-ran) |
| 14 | 2026-09-24 | T5 | C | yes | Claude Sonnet 5, High 1M | 10 | 1m32s | 13.0 | 37.8K | | 1 / 1 (git status to confirm) | 3/3, build OK | Crodox workbench t5-dashboard-crodox (pre-run: 2 SUCCESS, build OK); MCP disabled; agent ran tests + build |

| 15 | 2026-09-24 | T2 | A | yes | Claude Sonnet 5, High 1M | 6 | 26s | 14.4 | 45.9K | | 2 / 2 | 4/4, build OK | no guardrails; MCP disabled; agent searched, reviewed 3 files, changed sidebar .ts + .html (+12 -0), did not run tests. One evaluation run in visible Chrome showed AdminLayoutComponent FAILED; the headless rerun showed the usual 3 upstream failures only, so that was a flake, not a regression |
| 16 | 2026-09-24 | T2 | B | yes | Claude Sonnet 5, High 1M | 14 | 4m11s | 19.0 | 48.0K | | 2 / 2 | 4/4, build OK | instructions + files.exclude (T2); MCP disabled; agent changed sidebar .ts + .html, build OK; its Karma run failed to launch ChromeHeadless (agent: no Chrome binary found), so no test loop this time; agent said it "noted in repo memory"; git status shows no extra file, so that memory lives outside the repo. Our own ng test in the same folder ran fine (19 specs) |
| 17 | 2026-09-24 | T2 | C | yes | Claude Sonnet 5, High 1M | 8 | 1m18s | 11.5 | 36.8K | | 2 / 2 | 4/4, build OK | Crodox workbench t2-sidebar-crodox (pre-run: 2 SUCCESS, build OK); MCP disabled; agent changed sidebar .ts + .html (+13 -0), ran build + test |
| 18 | 2026-09-24 | T4 | A | yes | Claude Sonnet 5, High 1M | | | | | | | | no guardrails; MCP disabled |
| 19 | 2026-09-24 | T4 | B | yes | Claude Sonnet 5, High 1M | | | | | | | | instructions + files.exclude (T4); MCP disabled; Codespace port 9876 forwarding removed before the run |
| 20 | 2026-09-24 | T4 | C | yes | Claude Sonnet 5, High 1M | 8 | 1m39s | 9.4 | 32.8K | | | | Crodox workbench t4-notifications-crodox; MCP disabled; agent changed notifications.component.ts only, ran tests (2 specs, green) |
Session tokens include roughly 34K of fixed Copilot overhead (system instructions + tool definitions, 3-4% of the 1M window). The repository-dependent share is the difference above that floor.

Local Karma "ChromeHeadless has not captured" (2026-09-24): VS Code auto-forwards the Codespace's Karma port 9876 to localhost after a test run in the Codespace, so local Chrome connects to the forwarded port instead of the local Karma server. Fix: Ports panel in the Codespace window, Stop Forwarding Port 9876. This is also what made the arm B agent report "no Chrome binary" in run 16.
