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

Session tokens include roughly 34K of fixed Copilot overhead (system instructions + tool definitions, 3-4% of the 1M window). The repository-dependent share is the difference above that floor.
