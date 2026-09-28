# Integrating the benchmark with Crodox

This benchmark runs without Crodox. This guide replaces the hand-built slices of arm C with workbenches that Crodox generates from your own template, guardrails included. It also explains how the template's patches work and how to extend them.

Everything Crodox-specific is in `workbench-template/`. Nothing in `full-repo/`, `slices/` or the kit depends on it.

## 1. What Crodox needs

Crodox works with two GitHub repositories:

* **Source repository:** the code to slice. Crodox reads it through its GitHub App, runs the grammar over the file you pick, and extracts the component with its dependencies.
* **Template repository:** the workbench skeleton. Crodox copies it, drops the extracted files into it at their original paths, and applies the template's `repoPatches` to wire them in (imports, declarations, selectors). The result is the workbench; "Create Codespace" opens it in a browser VS Code.

Both must be reachable from your GitHub account with the Crodox GitHub App installed (Wiki: *GitHub App Installation*, *GitHub Repository Setup*).

The benchmark repository itself is not a good source repository: Crodox expects an Angular project at the repository root, and `full-repo/` is a subfolder. Push it as its own repository.

## 2. Push the two repositories

Source repository (a copy of `full-repo/` at the pinned commit):

```
cd full-repo
git init && git add -A
git commit -m "material-dashboard-angular2 at dcecb23 (benchmark source)"
git branch -M main
git remote add origin https://github.com/<you>/benchmark-source.git
git push -u origin main
cd .. && rm -rf full-repo/.git      # keep the benchmark repo as the single git root
```

Template repository:

```
cd workbench-template
git init && git add -A
git commit -m "Crodox workbench template for the task-isolation benchmark"
git branch -M main
git remote add origin https://github.com/<you>/benchmark-workbench-template.git
git push -u origin main
cd .. && rm -rf workbench-template/.git
```

Open `workbench-template/crodox.json` and set `"repo"` to the name Crodox shows for your template repository (angularTemp uses `"angularTemp_oss"`; the exact naming convention is something to confirm in the Patch Maker's *Template Repository* dropdown). Commit and push again if you changed it.

## 3. Set up the template in Crodox

1. **Settings:** confirm the GitHub link, re-link if needed, and make sure both repositories are visible.
2. **Template Editor** (`<>` icon), *Templates* tab: create a template, for example `BenchmarkExtractor_v1`.
3. Open `workbench-template/crodox.json`, copy the value of `crodoxText` into the Grammar Editor, click *Save*. It must report valid. This grammar is the one shipped with `crodox-app/angularTemp`; it already understands `.component.ts`, `.module.ts`, `.service.ts`, templates, styles and `package.json`.
4. **Patch Maker** (center-right): open *Template Repository* and pick your template repository. Crodox does not read `repoPatches` from the repository (confirmed); the panel shows "No conditions defined yet". Build the tree in the UI with *Add Root Condition*, *Add Child* and *Add Modification*, using the values from `crodox.json`: condition text, target file (`dir`), selector name, and the patched file content (`patchText`). For the benchmark three modifications are enough: `componentDeclaration` under `!{[dependencies].standalone.0==="true"}`, and `renderInHost` plus `guardrailScope` under `[dependencies].title==="selector"`, both children of `title==="component"`. Pick the target file carefully; the dropdown lists `.css` next to `.html`.
5. **Project Explorer:** select the source repository, open `src/app/components/footer/footer.component.ts`. The *Trial Extraction Field* should show a `component` object with `name`, `selector`, `templateUrl`, `styleUrls`. If it shows nothing, the grammar did not match; compare with the angularTemp workflow in the Wiki before changing anything.

## 4. Create one workbench per task

For task T3:

1. **Workbench** icon, name `T3-footer-crodox`, template `BenchmarkExtractor_v1`, repository = source repository.
2. Select `src/app/components/footer/footer.component.ts`, `.html`, `.css` and `.spec.ts`. Crodox marks them AUTO or MANUAL.
3. Check *Patch Preview*. Expected: `src/app/app.module.ts` gains `import { FooterComponent } from '../../src/app/components/footer/footer.component';` and `FooterComponent,` under `declarations`; `src/app/app.component.html` gains `<app-footer></app-footer>`.
4. *Create Workbench*, then *Create Codespace*. The template's `.devcontainer/devcontainer.json` installs Chromium and runs `npm install --legacy-peer-deps` on first start. If Crodox provisions the Codespace without honoring the devcontainer, run those two steps by hand in the Codespace terminal.
5. In the Codespace: `npx ng test --watch=false --karma-config karma.headless.js`. Expected: 2 specs pass (AppComponent, FooterComponent).

Repeat for T1, T2, T4, T5 with the component paths from `kit/tasks.json` (`slice_root`).

### T6: a component with a dependency

`NavbarComponent` imports `ROUTES` from `sidebar.component.ts`. This is the first task where Crodox has to bring a second file along. What to expect and check in the Patch Preview before creating `t6-navbar-crodox`:

* The Trial Extraction of `navbar.component.ts` shows an `import` object with `from` = `../sidebar/sidebar.component`. Crodox marks `sidebar.component.ts` (and its template and style) for extraction; if it does not, add them manually. The workbench needs them to compile.
* The condition tree runs over every extracted object. If Crodox treats the sidebar as a second `component`, `componentDeclaration`, `renderInHost` and `guardrailScope` fire for it too: the host renders `<app-sidebar>` next to `<app-navbar>` and the instructions file carries two scope blocks. That is acceptable for the build, but it weakens the guardrail (the agent is told it may edit the sidebar). Note in RUN_LOG.md what the preview showed. If the tree offers a way to distinguish the selected component from a dependency (`[rely]`, `[parent]` conditions; see the Wiki), restrict `guardrailScope` to the selected one and record the condition you used.
* `dependencyAllowlist` (new, under `[dependencies].title==="import"`) appends one line per import of the extracted component to the Policy section of the instructions: `` - `<~"from".0~>` ``. The placeholder follows the condition syntax `"from".0==="moment"` used by angularTemp; confirm in the preview that it resolves, and whether Crodox stacks the hunk once per import or only once. Either result is a finding worth a line in the integration notes.
* `tasks.json` lists the sidebar under `dependencies_read_only` for T6. `check_policy.py` reports a `readonly` violation if an arm changes it. In the workbench the file is present and editable; the guardrail is the only thing protecting it, which is exactly what T6 measures.

## 5. Run the benchmark in the Crodox arm

The procedure is the one in `README.md`, with these differences:

* The workspace is the Codespace of the workbench. Copilot agent mode works there as in local VS Code; credits and context tokens are read from the same places.
* `score_diff.py` needs a git repository. The workbench is one; run the script inside the Codespace: `python3 score_diff.py --task T3 --tasks-json tasks.json --repo .` after copying `kit/tasks.json` and `kit/scripts/score_diff.py` into the Codespace *after* the agent has finished (never before).
* Copy the hidden spec to `spec_target_path`, run the headless test, record `tests_passed`.
* Record the arm as `C_isolation` in `results.csv` and write `crodox` in `notes`, so Crodox workbenches and hand-built slices stay distinguishable. `analyze.py` treats both as arm C.
* Guardrails: the workbench already contains `.github/copilot-instructions.md`, generated by the `guardrailScope` patch with the component's name, selector and file. Do not run `make_guardrails.py` in a Crodox workbench; that would be a second, hand-made guardrail. Compare the two files once to confirm they say the same thing.
* After the run, *Refresh Preview* and *Merge Into Origin* (or *Generate Pull Request*). Then check in the source repository that only the footer files changed and run the hidden spec there once. A failure after reintegration is a Crodox finding, not an agent finding.

The static context of the Crodox workbench is measured like a slice: clone the workbench repository next to `slices/` and run `kit/scripts/context_tokens.py` with a `tasks.json` whose `slice_dir` points at it.

## 5a. Policy guardrails and the SBOM baseline in the workbench

From T6 on, the benchmark runs with the policy layer (`make_guardrails.py --policy` in arm B; in arm C the template provides the same text). Three pieces make it work in a Crodox workbench:

1. `.github/copilot-instructions.md` in the template now ships the static Policy section (no new dependencies, forbidden patterns, no `any`, license allowlist, allowed imports). `guardrailScope` still fills in component, selector and file; `dependencyAllowlist` fills in the imports.
2. `.devcontainer/devcontainer.json` writes `.guardrails/sbom.baseline.json` with `npm sbom --sbom-format cyclonedx --omit dev` right after `npm install`. That is the runtime SBOM of the workbench before the agent starts. (`npm sbom` works in the workbench because its lock file is fresh; it refuses the origin repository, whose lock file predates its package.json, which is why the kit ships `kit/scripts/sbom.py` for arms A and B.)
3. Evaluation of arm C happens locally, not in the Codespace, so the kit scripts and the hidden spec never have to be copied into the workbench:

```
# in the Codespace, after the run (this is also what Merge Into Origin reads)
git add -A && git commit -m "agent run T6" && git push

# locally
cd C:\Crodox\_wb
git clone https://github.com/<you>/t6-navbar-crodox.git
cd t6-navbar-crodox
git reset --soft HEAD~1                       # the agent's commit becomes staged changes
python C:\Crodox\task-isolation-benchmark\kit\scripts\score_diff.py --task T6 --repo .
python C:\Crodox\task-isolation-benchmark\kit\scripts\check_policy.py --task T6 --repo .
npm install --legacy-peer-deps
Copy-Item C:\Crodox\task-isolation-benchmark\kit\specs\navbar.bench.spec.ts src\app\components\navbar\
npx ng test --watch=false --karma-config karma.headless.js
npx ng build
```

`check_policy.py` compares the runtime SBOM of the clone against `.guardrails/sbom.baseline.json` from the devcontainer; because purls are normalised (`%40` and `@`), the npm-generated baseline and the Python-generated current SBOM compare cleanly.

## 6. How the patches work

`crodox.json` has three keys: `crodoxText` (the grammar), `repoPatches` (the wiring rules) and `repo` (the template repository).

`repoPatches` is a tree of **condition nodes**. Each node has a `key`, a `condition`, a list of `mods` and a list of `subCon` (child nodes that only apply when the parent matched). Conditions are evaluated against the objects the grammar extracted:

| Condition | Meaning |
| --- | --- |
| `title==="component"` | the extracted object is a `<:component:>` |
| `title==="service"`, `title==="module"` | same for services and NgModules |
| `[dependencies].title==="selector"` | the component has a `selector:` entry |
| `{[dependencies].standalone.0==="true"}` | the component declares `standalone: true`; `!{...}` negates |
| `[dependencies].title==="import"` then `"from".0==="moment"` | the file imports from the module `moment` |
| `[parent].title==="component"`, `[descendant].title==="paramMap"`, `[rely].title==="module"` | relations to parent, descendant or relied-upon objects (see angularTemp for examples) |

Each **mod** describes one file change in the template repository:

| Field | Meaning |
| --- | --- |
| `condition` | key of the node the mod belongs to |
| `key` | unique id of the mod |
| `dir` | path of the file inside the template repository |
| `fileText` | the file before the change (for chained mods: after the parent's change) |
| `patchText` | the file after the change, with placeholders |
| `patch` | unified diff hunk from `fileText` to `patchText`, four lines of context |
| `selector` | short label shown in the Patch Maker |

Placeholders are replaced with values from the object the condition matched. Under `title==="component"` that object is the component, so `<~name.0~>` is the class name. Under a child condition such as `[dependencies].title==="selector"` the matched object is the selector, and the component's name is reached through the parent: `<~[parent].name.0~>`. Confirmed in the Patch Preview: `<~name.0~>` inside the selector condition resolves to `undefined`. Otherwise `<~name.0~>` is the class name, `<~file~.ts~>` the repository-relative path of the extracted `.ts` file as an import path (angularTemp puts it straight into `from '...'`, so it must resolve without the extension; confirm on the first workbench), `<~selector.0~>` the selector string, `<~[parent].name.0~>` the name of the parent object, `<~output.0~>` an `@Output()` name. `<§Label§§default§>` marks a spot the user fills in the Patch Maker.

The template ships eight mods:

1. `componentDeclaration` (component, not standalone): import plus `declarations`.
2. `standaloneImport` (component, standalone): import plus `imports`.
3. `renderInHost` (component with selector): `<app-xyz></app-xyz>` in `app.component.html`.
4. `guardrailScope` (component with selector): appends the scope block to `.github/copilot-instructions.md`: component name, selector, editable file, verify commands. This is the automatic guardrail of the isolation arm; the template ships the file with the general rules, the patch fills in what is specific to the extracted component.
5. `momentDependency` (component that imports `moment`): adds `"moment"` to `package.json`. No benchmark component needs it; it is there as the worked example of a conditional dependency patch.
6. `serviceProvider` (service): import plus `providers`.
7. `moduleImport` (module): import plus `imports`.
8. `dependencyAllowlist` (component that imports something): one allowed-import line per import in the Policy section of `.github/copilot-instructions.md`.

Everything the five benchmark components need at runtime (jQuery, bootstrap-notify, Chartist, Material tooltip and button, Router) is already in the template's `package.json`, `angular.json` and `app.module.ts`, so no conditional patch has to fire for them. That is a deliberate choice: fewer moving parts in the first Crodox run.

## 7. Adding your own patch

Example: a component that imports from `angular-in-memory-web-api` should also get `HttpClientInMemoryWebApiModule` registered.

1. Decide the condition. Here: under `title==="component"`, add a child `[dependencies].title==="import"` (already exists as key 4), and under it a child `"from".0==="angular-in-memory-web-api"` with a new key, say 8.
2. Write the file before and after. Copy `workbench-template/src/app/app.module.ts` to `before.ts`; copy it again to `after.ts` and add the import line and the module entry, using placeholders where the value depends on the extracted object.
3. Generate the mod:

```
python3 kit/scripts/make_patch.py --before before.ts --after after.ts \
    --dir src/app/app.module.ts --condition 8 --key 6 --selector inMemoryApi
```

4. Paste the printed object into the `mods` array of the new node in `crodox.json`, commit, push, and reload the template repository in the Patch Maker.
5. Test with a source file that matches the condition and check the *Patch Preview*.

Two rules keep patches composable: a mod's `fileText` must be the file as it looks after all parent mods have been applied (that is how angularTemp chains the service patch and its `angular-in-memory-web-api` child), and two mods that touch the same region of the same file must not be siblings, because their hunks would conflict.

## 8. Making it your own template

The grammar (`crodoxText`) is the part that decides what Crodox can see. To extend it, use the Grammar Editor and the Wiki pages *Syntax Overview*, *Objects*, *Variables* and *Example Angular*. Typical extensions for this codebase:

* A `<:directive:>` definition, if you want to slice directives.
* A rule for `declare const $: any;`, so that jQuery usage becomes a visible dependency and a conditional patch (`jquery` in `package.json` and `angular.json` scripts) can fire instead of being in the template baseline.
* A rule for `import * as Chartist from 'chartist';`, which the existing `<:import:>` pattern already matches; a `"from".0==="chartist"` condition can then add the script entry to `angular.json`.

Once the grammar exposes a dependency, move the corresponding baseline entry out of the template and into a conditional patch. The workbench gets smaller, and the token comparison gets stricter.

## 9. What is verified and what is not

Verified here: the template installs, builds and passes its own spec. With the placeholders resolved by hand exactly as the patches specify, each of the five components was dropped into the template, the reference solution applied, and the hidden specs run: all pass, all five workbenches build. The guardrail patch was applied the same way for the footer and produces the expected instructions file.

Verified with a Crodox account (first T3 workbench): the grammar extracts the footer component from `benchmark-source`; the Patch Maker does not import `repoPatches` from the file, the tree is built in the UI; the template repository appears as `github/workbench-template`; `<~file~.ts~>` resolves to `src/app/components/footer/footer.component`, so the import path `'../../<~file~.ts~>'` is correct; inside the selector condition the component name is `<~[parent].name.0~>`. Still open: whether the Codespace honors `.devcontainer/devcontainer.json`.
