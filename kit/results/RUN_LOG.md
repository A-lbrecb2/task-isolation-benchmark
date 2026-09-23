# Run log

One row per run, in the order they happened. Runs that do not count stay in this log with
the reason; they are not copied to results.csv. This is where "the first B run had no
files.exclude" belongs, and where the Copilot numbers go before they are typed into the CSV.

| # | Date | Task | Arm | Valid | Model | Steps | Duration | Credits | Session tokens | References | Files changed / in scope | Tests passed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | T3 | A | ? | Claude Sonnet, High 1M | 3 | 1m04s | | | | | | first round; .vscode present in full-repo, check whether it held guardrail keys |
| 2 | 2026-09-23 | T3 | B | no | Claude Sonnet, High 1M | | | | | | | | first round; nested full-repo/ folder inside armB-full-repo (Copy-Item into existing dir) |
| 3 | 2026-09-23 | T3 | C | no | Claude Sonnet, High 1M | 12 | 1m31s | | | | 2 / 2 | | first round; stray footer.bench.spec.ts with "404: Not Found" in workspace; agent cited guardrail, touched only footer.component.ts/.html |
| 4 | 2026-09-23 | T3 | A | yes | Claude Sonnet, High 1M | 3 | 22s | | | | | | second round, C:\Crodox; MCP disabled |
| 5 | 2026-09-23 | T3 | B | no | Claude Sonnet, High 1M | 4 | 23s | | | | | | second round; instructions only, files.exclude missing (VS Code rewrote .vscode/settings.json). Interesting as "rules without visibility boundary" |
| 6 | 2026-09-23 | T3 | C | ? | Claude Sonnet, High 1M | | | | | | | | second round; MCP skipped |
