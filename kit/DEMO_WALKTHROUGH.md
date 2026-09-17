# Demo Walkthrough: Task T3, FooterComponent

Step-by-step guide for the ten-minute live demo in this standalone environment. Three arms: A is `full-repo/` without guardrails, B is a second copy of the full repository with generated guardrails, C is `slices/T3-footer/` with the same guardrails. The same prompt runs in all three, side by side, with GitHub Copilot in agent mode. Paths below are relative to the repository root, referred to as `$BENCH`.

Three parallel agents are a lot for one presenter. If you are alone on stage, run A and C live and show B from the prepared 45 runs; if you have a second person, run all three.

## Part 1: Preparation (the day before)

### 1.1 Tools

1. Install Node.js 16 or 18 (Angular 14). Node 22 works with a warning.
2. Install VS Code and the GitHub Copilot and GitHub Copilot Chat extensions. Sign in with an account that has agent mode and a paid model available.
3. Confirm that Copilot shows credits: open any chat, send a short prompt, hover over the response. If no credit figure appears, update the extension before the demo.
4. Install Chrome or Chromium for Karma. If Karma cannot find it, set `CHROME_BIN` to the browser executable.
5. `pip install tiktoken matplotlib` for the scripts.

### 1.2 All arms

Arm B needs its own copy of the full repository for the live demo, because A and B run at the same time (for the sequential benchmark runs the single `full-repo/` folder is enough, see README). Make it a plain copy outside the git repository:

```
cd $BENCH
./setup.sh                       # npm install --legacy-peer-deps in full-repo and all slices
./test.sh full-repo              # expect: 3 FAILED, 12 SUCCESS (upstream failures, not ours)
./test.sh slices/T3-footer       # expect: 1 SUCCESS
Copy-Item -Recurse full-repo ..\armB-full-repo      # PowerShell; on macOS/Linux: cp -r full-repo ../armB-full-repo
git status                       # must be clean before the demo
```

Then generate the guardrails. Arm A gets none, B gets instructions plus workspace restriction, C gets instructions:

```
python3 kit/scripts/make_guardrails.py --task T3 --arm B --target ../armB-full-repo
python3 kit/scripts/make_guardrails.py --task T3 --arm C --target slices/T3-footer
```

`../armB-full-repo` is not a git repository, so `score_diff.py` cannot run there. Make it one before the demo: `cd ../armB-full-repo; git init; git add -A; git commit -m base` (the guardrail files are committed as part of the base, which is what you want: they are setup, not agent output).

### 1.3 Screen layout

1. Open `$BENCH/full-repo` (A), `../armB-full-repo` (B) and `$BENCH/slices/T3-footer` (C) in three VS Code windows. Open each folder itself as the workspace root, not `$BENCH`. The agent must not see `kit/` or the other arms.
2. Place the windows left to right: A, B, C. In B the Explorer shows only `src/app/components/footer` plus configuration; that is the workspace guardrail at work.
3. In all windows open Copilot Chat, switch to Agent mode, select the same model, and note the exact model name.
4. In all windows open the Explorer so the audience sees the difference: A everything, B everything hidden but the footer, C only the footer exists.
5. Put the T3 prompt (below) on the clipboard or in a scratch file outside all three folders.
6. Keep a third terminal open at `$BENCH` for the scoring commands.
7. Run the whole demo once end to end the day before and time it.

### 1.4 The prompt (paste verbatim, all arms)

```
Make `FooterComponent` configurable.

Requirements:
1. Add an `@Input()` property `companyName: string` with the default value `'Creative Tim'`.
2. Add an `@Input()` property `companyUrl: string` with the default value `'https://www.creative-tim.com'`.
3. Add a getter `copyrightYear: number` that returns the full year of the existing `test` date property.
4. Use `companyName`, `companyUrl`, and `copyrightYear` in the copyright line of the template instead of the hard-coded values. The `date` pipe is no longer needed there.

Do not change any other component, module, or shared file.
```

## Part 2: The ten minutes

### Minute 0 to 1: Name the problem

Say: "A coding agent pays for every token it reads. In a full repository it searches, opens files it does not need, and sends all of that to the model. GitHub's own documentation notes that a larger context window means more credits. If the agent gets only the component and its dependencies, how much does that save, and does it work better or worse? We measure it."

### Minute 1 to 2: Show the setup

1. Point at the left window: "The full repository, 57 application files, about 32,000 tokens of code and configuration. No instructions."
2. Point at the middle window: "The same repository. But the agent has a rulebook: only the footer, do not touch anything else, and everything else is hidden from the Explorer and from search. This is the best you can do with instructions."
3. Point at the right window: "The slice, six application files, about 2,800 tokens, same rulebook. Same component, same path, compiles and tests on its own. Here the rest of the codebase does not exist."
4. Say: "Same model, all chats are new. Same prompt, pasted at the same time. No follow-ups, we accept whatever the agents propose. The question is not only full repo against slice. It is: do rules do the job, or do you need the wall?"

### Minute 2 to 6: Live run

1. Paste the prompt into the left chat, press Enter. Immediately the middle, then the right.
2. While the agents work, narrate what is visible: the "Used N references" line, the files being opened, the tool calls. Typical observation: the full-repo agent opens `app.module.ts`, `components.module.ts` or the navbar before it finds the footer. The guardrail agent usually reads less, but watch whether it still opens hidden files by path. The slice agent goes straight to the component.
3. When all are done, click "Keep" on all proposed edits in every window.
4. Hover over each response and read the credit figure aloud. Then click the context window control in each chat input and read the session token count.
5. Write the numbers on the whiteboard or in the recording sheet (Part 3).

If one agent is still running after four minutes, continue with the others and come back.

### Minute 6 to 7: Diff score and tests

In the third terminal at `$BENCH`:

```
python3 kit/scripts/score_diff.py --task T3 --repo full-repo
python3 kit/scripts/score_diff.py --task T3 --repo ../armB-full-repo
python3 kit/scripts/score_diff.py --task T3 --repo slices/T3-footer
cp kit/specs/footer.bench.spec.ts full-repo/src/app/components/footer/
cp kit/specs/footer.bench.spec.ts ../armB-full-repo/src/app/components/footer/
cp kit/specs/footer.bench.spec.ts slices/T3-footer/src/app/components/footer/
./test.sh slices/T3-footer
./test.sh full-repo
(cd ../armB-full-repo && npx ng test --watch=false --karma-config karma.headless.js)
```

Read aloud: files changed, files in scope, tests passed out of 3 (the `T3 FooterComponent (benchmark)` lines). Run the diff score before copying the spec, otherwise the spec counts as a touched file. In both full-repo copies, ignore the three upstream failures. For arm B, files in scope is also the guardrail compliance: did the agent obey the rulebook?

### Minute 7 to 9: The full result

Show `kit/results/summary.png` from the 45 prepared runs. Walk through the three panels: credits per prompt, tests passed, diff precision, three bars per task. State the overall numbers exactly as `summary.md` prints them, including the ones that are not flattering, and in particular the last line: the difference between guardrails alone and isolation.

Say: "The live run is one sample. These are forty-five. The repository is public, the commit is pinned, anyone can rerun it."

### Minute 9 to 10: Bring the change back

1. Show that the slice change is the same change the full repository needs: `git diff slices/T3-footer/src/app` next to `git diff full-repo/src/app`.
2. Copy the two changed files from the slice into `full-repo` (or apply the diff) and run `./test.sh full-repo` once more: the change made in isolation passes in the full repository.
3. Close with the repository link.

## Part 3: What to record during the demo

| Field | Arm A | Arm B | Arm C |
| --- | --- | --- | --- |
| Model | | | |
| Credits for the prompt (hover) | | | |
| Session context tokens (context window control) | | | |
| References used | | | |
| Tool calls (Agent Debug Logs summary) | | | |
| Duration in seconds | | | |
| Files changed / in scope (score_diff.py) | | | |
| Tests passed out of 3 | | | |
| ng build OK (1/0) | | | |

Append the three rows to `kit/results/results.csv` afterwards with `task=T3`, `arm=A_full_repo`, `B_full_repo_guardrails` or `C_isolation`, and the next free `run_id`. A demo run is a valid data point.

## Part 4: Fallbacks

* Copilot is slow or offline: play the recording from the dry run and continue with Minute 6 on the recorded state.
* An agent fails the task: say so and show the failing test. A failed run is a data point, not an embarrassment. The thirty prepared runs carry the claim, not this one.
* No credit figure on hover: use the session context tokens instead and say that credits are computed from tokens.
* Karma cannot start Chrome: set `CHROME_BIN`, or run `npx ng test --watch=false` in the project folder and let it open a browser window.
* The slice is missing a dependency the agent needs: that is a finding about the slice. Note it, fix the slice after the demo, do not patch it live.

## Part 5: Reset between demos

```
cd $BENCH
git checkout -- full-repo slices && git clean -fd full-repo slices
python3 kit/scripts/make_guardrails.py --task T3 --arm C --target slices/T3-footer
cd ../armB-full-repo && git checkout -- . && git clean -fd && cd $BENCH
git status        # clean
```

`git clean` in `$BENCH` also removes the arm C guardrails, hence the regeneration. In `../armB-full-repo` the guardrails are part of the base commit and survive the reset. Start a new chat in all VS Code windows.
