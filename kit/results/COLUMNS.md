# Columns of the results file

| Column | Source | Meaning |
| --- | --- | --- |
| run_id | manual | Sequential, e.g. R001 |
| date | manual | Date of the run, ISO (2026-09-18) |
| task | tasks.json | T1 to T5 |
| arm | tasks.json | A_full_repo, B_full_repo_guardrails or C_isolation |
| repetition | manual | 1 to 3 |
| model | VS Code chat model picker | exact model name |
| credits_turn | VS Code: hover over the chat response | credits for the prompt |
| credits_session | VS Code: context window control in the chat input, session info | session total (equals credits_turn for a single prompt) |
| context_tokens_session | VS Code: context window control, session info | cumulative context tokens of the session |
| tool_calls | VS Code: Agent Debug Logs, summary | number of tool calls (read file, search, ...) |
| duration_s | VS Code: Agent Debug Logs, summary | duration in seconds |
| references_count | VS Code: "Used N references" under the response | number of files read |
| tests_total | Karma output | test cases in the hidden spec (T1: 4, T2: 4, T3: 3, T4: 4, T5: 3) |
| tests_passed | Karma output | passed test cases of the hidden spec only |
| files_changed | score_diff.py | touched files, spec excluded |
| files_in_scope | score_diff.py | of those, inside the allowed files |
| build_ok | ng build | 1 if the build succeeds, else 0 |
| notes | manual | anything unusual, e.g. "agent edited navbar.component.ts" |
