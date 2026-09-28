# Runtime SBOM per arm

Generated with `kit/scripts/sbom.py compare` at commit dcecb23 (origin) and the current slices/template. Runtime dependencies only (`dependencies` in package.json, resolved through node_modules the way Node does); devDependencies excluded.

| Project | Direct runtime deps | Resolved runtime components | Reduction vs first |
| --- | --- | --- | --- |
| full-repo | 31 | 250 | - |
| workbench-template | 16 | 17 | 93% |
| slices/T1-table-list | 11 | 11 | 96% |
| slices/T2-sidebar | 12 | 12 | 95% |
| slices/T3-footer | 11 | 11 | 96% |
| slices/T4-notifications | 13 | 13 | 95% |
| slices/T5-dashboard | 14 | 15 | 94% |
| slices/T6-navbar | 12 | 12 | 95% |

The origin declares 31 runtime dependencies, among them express, googleapis, eslint and ajv, which no component uses at runtime; they resolve to 250 components. The Crodox workbench template declares 16 and resolves to 17. Licenses in the origin's runtime tree: MIT 189, ISC 27, Apache-2.0 15, BSD 11, plus eight one-offs (CC-BY-4.0, Python-2.0, dual GPL/BSD, public domain). The workbench tree is MIT, Apache-2.0 and 0BSD only.
