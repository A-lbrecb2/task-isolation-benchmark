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
4. **Patch Maker** (center-right): open *Template Repository* and pick your template repository. The conditions from `repoPatches` should appear: `title==="component"` with four sub-conditions, `title==="service"`, `title==="module"`. If the Patch Maker does not read `repoPatches` from the repository automatically, recreate them there with the values from `crodox.json` (each entry has `condition`, `dir`, `patch`, `patchText`, `fileText`, `selector`).
5. **Project Explorer:** select the source repository, open `src/app/components/footer/footer.component.ts`. The *Trial Extraction Field* should show a `component` object with `name`, `selector`, `templateUrl`, `styleUrls`. If it shows nothing, the grammar did not match; compare with the angularTemp workflow in the Wiki before changing anything.

## 4. Create one workbench per task

For task T3:

1. **Workbench** icon, name `T3-footer-crodox`, template `BenchmarkExtractor_v1`, repository = source repository.
2. Select `src/app/components/footer/footer.component.ts`, `.html`, `.css` and `.spec.ts`. Crodox marks them AUTO or MANUAL.
3. Check *Patch Preview*. Expected: `src/app/app.module.ts` gains `import { FooterComponent } from '../../src/app/components/footer/footer.component';` and `FooterComponent,` under `declarations`; `src/app/app.component.html` gains `<app-footer></app-footer>`.
4. *Create Workbench*, then *Create Codespace*. The template's `.devcontainer/devcontainer.json` installs Chromium and runs `npm install --legacy-peer-deps` on first start. If Crodox provisions the Codespace without honoring the devcontainer, run those two steps by hand in the Codespace terminal.
5. In the Codespace: `npx ng test --watch=false --karma-config karma.headless.js`. Expected: 2 specs pass (AppComponent, FooterComponent).

Repeat for T1, T2, T4, T5 with the component paths from `kit/tasks.json` (`slice_root`).

## 5. Run the benchmark in the Crodox arm

The procedure is the one in `README.md`, with these differences:

* The workspace is the Codespace of the workbench. Copilot agent mode works there as in local VS Code; credits and context tokens are read from the same places.
* `score_diff.py` needs a git repository. The workbench is one; run the script inside the Codespace: `python3 score_diff.py --task T3 --tasks-json tasks.json --repo .` after copying `kit/tasks.json` and `kit/scripts/score_diff.py` into the Codespace *after* the agent has finished (never before).
* Copy the hidden spec to `spec_target_path`, run the headless test, record `tests_passed`.
* Record the arm as `C_isolation` in `results.csv` and write `crodox` in `notes`, so Crodox workbenches and hand-built slices stay distinguishable. `analyze.py` treats both as arm C.
* Guardrails: the workbench already contains `.github/copilot-instructions.md`, generated by the `guardrailScope` patch with the component's name, selector and file. Do not run `make_guardrails.py` in a Crodox workbench; that would be a second, hand-made guardrail. Compare the two files once to confirm they say the same thing.
* After the run, *Refresh Preview* and *Merge Into Origin* (or *Generate Pull Request*). Then check in the source repository that only the footer files changed and run the hidden spec there once. A failure after reintegration is a Crodox finding, not an agent finding.

The static context of the Crodox workbench is measured like a slice: clone the workbench repository next to `slices/` and run `kit/scripts/context_tokens.py` with a `tasks.json` whose `slice_dir` points at it.

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

Placeholders are replaced with values from the extracted object: `<~name.0~>` is the class name, `<~file~.ts~>` the repository-relative path of the extracted `.ts` file as an import path (angularTemp puts it straight into `from '...'`, so it must resolve without the extension; confirm on the first workbench), `<~selector.0~>` the selector string, `<~[parent].name.0~>` the name of the parent object, `<~output.0~>` an `@Output()` name. `<§Label§§default§>` marks a spot the user fills in the Patch Maker.

The template ships seven mods:

1. `componentDeclaration` (component, not standalone): import plus `declarations`.
2. `standaloneImport` (component, standalone): import plus `imports`.
3. `renderInHost` (component with selector): `<app-xyz></app-xyz>` in `app.component.html`.
4. `guardrailScope` (component with selector): appends the scope block to `.github/copilot-instructions.md`: component name, selector, editable file, verify commands. This is the automatic guardrail of the isolation arm; the template ships the file with the general rules, the patch fills in what is specific to the extracted component.
5. `momentDependency` (component that imports `moment`): adds `"moment"` to `package.json`. No benchmark component needs it; it is there as the worked example of a conditional dependency patch.
6. `serviceProvider` (service): import plus `providers`.
7. `moduleImport` (module): import plus `imports`.

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

Not verified here, because it needs a Crodox account: that the Patch Maker reads `repoPatches` from the repository in this form, the exact string Crodox expects in `"repo"`, whether `<~file~.ts~>` resolves to `src/app/...` as assumed in the import path `'../../<~file~.ts~>'`, and whether the Codespace honors `.devcontainer/devcontainer.json`. Check these four with the first workbench; each is a one-line fix if the assumption is wrong.
