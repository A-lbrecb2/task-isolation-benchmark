# workbench-template

Crodox template repository for the task-isolation benchmark. It is the workbench skeleton: a minimal
Angular 14 host application with every runtime dependency the material-dashboard-angular2 components
need (jQuery, bootstrap-notify, Chartist, Angular Material tooltip and button). `crodox.json` carries
the grammar (imported from crodox-app/angularTemp) and the `repoPatches` that wire an extracted
component, service or module into `src/app/app.module.ts` and `src/app/app.component.html`.

The extracted files keep their original path (`src/app/<folder>/...`), so the hidden benchmark specs
can be copied to the same place as in the full repository.

    npm install --legacy-peer-deps
    npx ng test --watch=false --karma-config karma.headless.js
