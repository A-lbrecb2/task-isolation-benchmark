<#
.SYNOPSIS
  One command per phase of a benchmark run, for arms A and B on Windows.

  .\kit\scripts\round.ps1 reset T3            resets arm A (full-repo) and arm B (armB-full-repo),
                                              writes B's guardrails (with policy), commits them,
                                              prints what to do in the Crodox Codespace (arm C)
  .\kit\scripts\round.ps1 eval  T3            after the agents are done: diff score, policy check,
                                              hidden spec, headless tests, build, for A and B;
                                              writes kit\results\eval\T3-<time>-A.txt and -B.txt
  .\kit\scripts\round.ps1 evalc T3 <git-url>  clones the Crodox workbench repo (after you pushed the
                                              agent's commit from the Codespace), runs the same
                                              evaluation on it; writes -C.txt
  .\kit\scripts\round.ps1 clean T3            removes the hidden spec from A and B again
  .\kit\scripts\round.ps1 run   T3 [<git-url>] fully automated run with the GitHub Copilot CLI:
                                              reset, guardrails, copilot -p in A (task, then the
                                              verify prompt), B and C (local clone of the Crodox
                                              workbench, cloned from <git-url> on first use, reset
                                              afterwards), evaluation, one row per arm appended to
                                              kit\results\results.csv, transcripts in kit\results\eval.
                                              -Model <id> is passed to copilot --model.

  Options: -NoPolicy (round-1 style guardrails, no Policy section, no SBOM baseline)
           -Bench <path> (default C:\Crodox\task-isolation-benchmark)
           -ArmB  <path> (default C:\Crodox\armB-full-repo)

  Run from PowerShell 7. Needs python on PATH. Does not touch the Codespace; arm C is evaluated
  from a local clone so that no kit file ever enters the workbench.
#>
param(
  [Parameter(Mandatory = $true, Position = 0)][ValidateSet('reset', 'eval', 'evalc', 'clean', 'run')][string]$Phase,
  [Parameter(Mandatory = $true, Position = 1)][string]$Task,
  [Parameter(Position = 2)][string]$WorkbenchUrl,
  [string]$Bench = 'C:\Crodox\task-isolation-benchmark',
  [string]$ArmB = 'C:\Crodox\armB-full-repo',
  [switch]$NoPolicy,
  [string]$Model = '',
  [switch]$ResumeCumulative,
  [string]$Date = (Get-Date -Format 'yyyy-MM-dd')
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$inv = [System.Globalization.CultureInfo]::InvariantCulture
function Num($x) { if ($null -eq $x -or $x -eq '') { '' } else { ([double]$x).ToString($inv) } }
$kit = Join-Path $Bench 'kit'
$tasks = (Get-Content (Join-Path $kit 'tasks.json') -Raw | ConvertFrom-Json).tasks
$t = $tasks | Where-Object { $_.id -eq $Task }
if (-not $t) { throw "unknown task $Task" }
$specSrc = Join-Path $kit $t.spec_file
$specRel = $t.spec_target_path -replace '/', '\'
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$evalDir = Join-Path $kit 'results\eval'
$testsTotal = ([regex]::Matches((Get-Content $specSrc -Raw), '\bit\(')).Count
New-Item -ItemType Directory -Force -Path $evalDir | Out-Null

function Section($txt) { Write-Host "`n== $txt ==" -ForegroundColor Cyan }

function Invoke-Copilot($repo, $promptFile, $out, $resume) {
  # runs the Copilot CLI non-interactively in $repo, saves the transcript, returns parsed numbers
  $prompt = Get-Content $promptFile -Raw
  $cargs = @('-p', $prompt, '--allow-all-tools')
  if ($Model) { $cargs += @('--model', $Model) }
  if ($resume) { $cargs += "--resume=$resume" }
  Push-Location $repo
  try {
    $t0 = Get-Date
    $text = (& copilot @cargs 2>&1 | Out-String)
    $wall = [int]((Get-Date) - $t0).TotalSeconds
  } finally { Pop-Location }
  $text | Out-File -FilePath $out -Encoding utf8
  # a step line is a status glyph (or spinner frame) followed by the tool title; details follow indented with box characters
  $steps = ([regex]::Matches($text, '(?m)^[\u25CF\u25CB\u2713\u2714\u2717\u2718/\\|\-] \S[^\r\n]*\r?\n\s+[\u2502\u2514\u251C]')).Count
  $m = [regex]::Match($text, 'AI Credits\s+([\d.]+)\s*\((?:(\d+)m\s*)?(\d+)s\)')
  $tok = [regex]::Match($text, 'Tokens\s+\S+\s*([\d.]+)k')
  $chg = [regex]::Match($text, 'Changes\s+\+(\d+)\s+-(\d+)')
  $res = [regex]::Match($text, '--resume=([0-9a-f-]+)')
  [pscustomobject]@{
    credits  = if ($m.Success) { [double]::Parse($m.Groups[1].Value, $inv) } else { $null }
    seconds  = if ($m.Success) { $(if ($m.Groups[2].Success) { 60 * [int]$m.Groups[2].Value } else { 0 }) + [int]$m.Groups[3].Value } else { $wall }
    tokens_k = if ($tok.Success) { [double]::Parse($tok.Groups[1].Value, $inv) } else { $null }
    added    = if ($chg.Success) { [int]$chg.Groups[1].Value } else { $null }
    removed  = if ($chg.Success) { [int]$chg.Groups[2].Value } else { $null }
    steps    = $steps
    resume   = if ($res.Success) { $res.Groups[1].Value } else { '' }
    transcript = $out
  }
}

function Evaluate-Object($repo) {
  # same checks as Evaluate, but returned as numbers for results.csv
  Push-Location $repo
  try {
    $sd = (python (Join-Path $kit 'scripts\score_diff.py') --task $Task --repo . --json 2>&1 | Out-String | ConvertFrom-Json)
    $pc = (python (Join-Path $kit 'scripts\check_policy.py') --task $Task --repo . --json 2>&1 | Out-String | ConvertFrom-Json)
    Copy-Item $specSrc (Join-Path $repo $specRel) -Force
    $test = (npx ng test --watch=false --karma-config karma.headless.js 2>&1 | Out-String)
    $failedBench = ([regex]::Matches($test, '(?m)^.*\(benchmark\).*FAILED\s*$')).Count
    $total = [regex]::Match($test, 'TOTAL:\s*(?:(\d+) FAILED, )?(\d+) SUCCESS')
    $ran = $total.Success
    $build = (npx ng build 2>&1 | Out-String)
    $buildOk = if ($build -match 'Build at') { 1 } else { 0 }
    Remove-Item (Join-Path $repo $specRel) -ErrorAction SilentlyContinue
    [pscustomobject]@{
      files_changed = $sd.files_changed; files_in_scope = $sd.files_in_scope
      tests_total = $testsTotal; tests_passed = if ($ran) { $testsTotal - $failedBench } else { $null }
      build_ok = $buildOk; policy_violations = $pc.count; sbom_components = $pc.sbom_components_now
      test_line = if ($ran) { $total.Value } else { 'tests did not run' }
    }
  } finally { Pop-Location }
}

function Next-RunId {
  $csv = Join-Path $kit 'results\results.csv'
  $ids = (Get-Content $csv | Select-String -Pattern '^R(\d+),' | ForEach-Object { [int]$_.Matches[0].Groups[1].Value })
  $n = if ($ids) { [int](($ids | Measure-Object -Maximum).Maximum) + 1 } else { 1 }
  'R{0:d3}' -f $n
}

function Append-Result($arm, $cp, $ev, $verifyCredits, $notes) {
  $csv = Join-Path $kit 'results\results.csv'
  $header = (Get-Content $csv -First 1) -split ','
  $row = @{}
  foreach ($h in $header) { $row[$h] = '' }
  $row['run_id'] = Next-RunId; $row['date'] = $Date; $row['task'] = $Task; $row['arm'] = $arm; $row['repetition'] = ''
  $row['model'] = if ($Model) { "$Model (Copilot CLI)" } else { 'Copilot CLI default model' }
  $row['credits_turn'] = Num $cp.credits; $row['credits_session'] = if ($verifyCredits) { Num ([math]::Round($cp.credits + $verifyCredits, 2)) } else { Num $cp.credits }
  $row['context_tokens_session'] = if ($cp.tokens_k) { [int]($cp.tokens_k * 1000) } else { '' }
  $row['tool_calls'] = $cp.steps; $row['duration_s'] = $cp.seconds
  $row['tests_total'] = $ev.tests_total; $row['tests_passed'] = $ev.tests_passed
  $row['files_changed'] = $ev.files_changed; $row['files_in_scope'] = $ev.files_in_scope; $row['build_ok'] = $ev.build_ok
  $row['policy_violations'] = $ev.policy_violations; $row['sbom_components'] = $ev.sbom_components
  $row['credits_verify'] = Num $verifyCredits
  $row['notes'] = ($notes -replace ',', ';')
  $line = ($header | ForEach-Object { $row[$_] }) -join ','
  Add-Content -Path $csv -Value $line
  Write-Host "results.csv += $line" -ForegroundColor Green
}

function Evaluate($label, $repo, $out) {
  Section "$label : $repo"
  Push-Location $repo
  try {
    $lines = @()
    $lines += "# $Task arm $label  $repo  $(Get-Date -Format s)"
    $lines += '## git status'
    $lines += (git status --short)
    $lines += '## score_diff'
    $lines += (python (Join-Path $kit 'scripts\score_diff.py') --task $Task --repo . 2>&1)
    $lines += '## check_policy'
    $lines += (python (Join-Path $kit 'scripts\check_policy.py') --task $Task --repo . 2>&1)
    Copy-Item $specSrc (Join-Path $repo $specRel) -Force
    $lines += "## ng test (spec copied to $specRel)"
    $test = (npx ng test --watch=false --karma-config karma.headless.js 2>&1 | Out-String)
    $lines += ($test -split "`n" | Select-String -Pattern 'TOTAL:|benchmark|FAILED$|has not captured' | ForEach-Object { $_.Line.Trim() })
    $lines += '## ng build'
    $build = (npx ng build 2>&1 | Out-String)
    $lines += ($build -split "`n" | Select-String -Pattern 'Build at|ERROR|Error:' | ForEach-Object { $_.Line.Trim() })
    $lines | Tee-Object -FilePath $out
    Write-Host "written $out" -ForegroundColor Green
  } finally { Pop-Location }
}

switch ($Phase) {
  'reset' {
    Section 'arm A: reset full-repo'
    Push-Location $Bench
    git checkout -- full-repo; git clean -fdq full-repo
    $st = git status --short full-repo
    if ($st) { Write-Host $st; throw 'full-repo not clean' } else { Write-Host 'clean' }
    Pop-Location

    Section 'arm B: reset and guardrails'
    Push-Location $ArmB
    git checkout -- .; git clean -fdq
    $gargs = @('--task', $Task, '--arm', 'B', '--target', '.')
    if (-not $NoPolicy) { $gargs += '--policy' }
    python (Join-Path $kit 'scripts\make_guardrails.py') @gargs
    git add -A | Out-Null
    git commit -q -m "guardrails $Task arm B" 2>$null
    Write-Host (Select-String -Path .github\copilot-instructions.md -Pattern $t.component | Select-Object -First 1).Line
    $st = git status --short
    if ($st) { Write-Host $st; throw 'armB not clean after commit' } else { Write-Host 'committed, clean' }
    Pop-Location

    Section 'arm C: in the Crodox Codespace'
    Write-Host "  cd /workspaces/<workbench>; git checkout -- .; git clean -fd; git status --short"
    Write-Host "  npx ng test --watch=false --karma-config karma.headless.js 2>&1 | grep TOTAL"
    Write-Host "  then: Ports panel -> stop forwarding 9876"
    Section 'next'
    Write-Host "  B window: Developer: Reload Window. New chat in A, B, C. Paste kit\prompts\$Task.md into A, B, C."
    Write-Host "  Arm A: read Session Info, THEN paste kit\prompts\verify\$Task.md as a second prompt, read Session Info again."
  }
  'eval' {
    Evaluate 'A' (Join-Path $Bench 'full-repo') (Join-Path $evalDir "$Task-$stamp-A.txt")
    Evaluate 'B' $ArmB (Join-Path $evalDir "$Task-$stamp-B.txt")
    Write-Host "`nSend the two files in kit\results\eval to the log keeper." -ForegroundColor Yellow
  }
  'evalc' {
    if (-not $WorkbenchUrl) { throw 'evalc needs the workbench git URL as third argument' }
    $wb = Join-Path 'C:\Crodox\_wb' ("$Task-" + $stamp)
    New-Item -ItemType Directory -Force -Path 'C:\Crodox\_wb' | Out-Null
    Section "arm C: clone $WorkbenchUrl"
    git clone -q $WorkbenchUrl $wb
    Push-Location $wb
    git reset -q --soft HEAD~1      # the agent's commit becomes staged changes
    Write-Host 'npm install (one to three minutes)'
    npm install --legacy-peer-deps 2>&1 | Select-Object -Last 2
    Pop-Location
    Evaluate 'C' $wb (Join-Path $evalDir "$Task-$stamp-C.txt")
  }
  'run' {
    if (-not (Get-Command copilot -ErrorAction SilentlyContinue)) { throw 'copilot CLI not found (npm install -g @github/copilot)' }
    $promptFile = Join-Path $kit "prompts\$Task.md"
    $verifyFile = Join-Path $kit "prompts\verify\$Task.md"
    $wbDir = Join-Path 'C:\Crodox\_wb' $Task

    # --- reset A and B (same as 'reset') ---
    $rs = @{ Phase = 'reset'; Task = $Task; Bench = $Bench; ArmB = $ArmB; NoPolicy = $NoPolicy }
    & $PSCommandPath @rs | Out-Null

    # --- arm C: local clone of the Crodox workbench ---
    Section "arm C: workbench clone $wbDir"
    if (-not (Test-Path $wbDir)) {
      if (-not $WorkbenchUrl) { throw "first run for $Task : pass the workbench git URL as third argument" }
      New-Item -ItemType Directory -Force -Path 'C:\Crodox\_wb' | Out-Null
      git clone -q $WorkbenchUrl $wbDir
      Push-Location $wbDir; npm install --legacy-peer-deps 2>&1 | Select-Object -Last 1; Pop-Location
    }
    Push-Location $wbDir
    git checkout -- . ; git clean -fdq
    if (-not (Test-Path '.guardrails\sbom.baseline.json')) {
      New-Item -ItemType Directory -Force -Path '.guardrails' | Out-Null
      python (Join-Path $kit 'scripts\sbom.py') generate . --out '.guardrails\sbom.baseline.json' | Out-Null
    }
    if (-not (Test-Path '.github\copilot-instructions.md')) { Write-Host 'WARNING: workbench has no copilot-instructions.md; template patch missing?' -ForegroundColor Yellow }
    Pop-Location

    # --- arm A: task, then verify ---
    Section 'arm A: copilot, task prompt'
    $repoA = Join-Path $Bench 'full-repo'
    $cpA = Invoke-Copilot $repoA $promptFile (Join-Path $evalDir "$Task-$stamp-A-task.txt") $null
    Write-Host ("  {0} credits, {1} s, {2} steps, +{3} -{4}" -f $cpA.credits, $cpA.seconds, $cpA.steps, $cpA.added, $cpA.removed)
    Section 'arm A: copilot, verify prompt (second stage, same session)'
    $cpAv = Invoke-Copilot $repoA $verifyFile (Join-Path $evalDir "$Task-$stamp-A-verify.txt") $cpA.resume
    if ($null -eq $cpAv.credits) {
      Write-Host '  resumed session reported no footer; running the verify prompt as a fresh session instead' -ForegroundColor Yellow
      $cpAv = Invoke-Copilot $repoA $verifyFile (Join-Path $evalDir "$Task-$stamp-A-verify.txt") $null
    }
    Write-Host ("  {0} credits reported, {1} s, {2} steps" -f $cpAv.credits, $cpAv.seconds, $cpAv.steps)
    # -ResumeCumulative: the CLI reports the whole resumed session, so subtract the task turn
    $verifyCredits = if ($ResumeCumulative -and $cpAv.credits -gt $cpA.credits) { [math]::Round($cpAv.credits - $cpA.credits, 2) } else { $cpAv.credits }
    $evA = Evaluate-Object $repoA
    Append-Result 'A_full_repo' $cpA $evA $verifyCredits ("copilot cli; two-stage; verify footer {0} credits {1} s {2} steps (stored as {3}{4}); {5}" -f (Num $cpAv.credits), $cpAv.seconds, $cpAv.steps, (Num $verifyCredits), $(if ($ResumeCumulative) { ' after subtracting the task turn' } else { '' }), $evA.test_line)

    # --- arm B ---
    Section 'arm B: copilot'
    $cpB = Invoke-Copilot $ArmB $promptFile (Join-Path $evalDir "$Task-$stamp-B.txt") $null
    Write-Host ("  {0} credits, {1} s, {2} steps, +{3} -{4}" -f $cpB.credits, $cpB.seconds, $cpB.steps, $cpB.added, $cpB.removed)
    $evB = Evaluate-Object $ArmB
    Append-Result 'B_full_repo_guardrails' $cpB $evB $null ("copilot cli; instructions" + $(if ($NoPolicy) { '' } else { ' + policy' }) + "; files.exclude not applicable in the CLI; " + $evB.test_line)

    # --- arm C ---
    Section 'arm C: copilot'
    $cpC = Invoke-Copilot $wbDir $promptFile (Join-Path $evalDir "$Task-$stamp-C.txt") $null
    Write-Host ("  {0} credits, {1} s, {2} steps, +{3} -{4}" -f $cpC.credits, $cpC.seconds, $cpC.steps, $cpC.added, $cpC.removed)
    $evC = Evaluate-Object $wbDir
    Append-Result 'C_isolation' $cpC $evC $null ("copilot cli; crodox workbench clone $wbDir; " + $evC.test_line)

    # --- reset the arms again so the next run starts clean ---
    Push-Location $Bench; git checkout -- full-repo; git clean -fdq full-repo; Pop-Location
    Push-Location $ArmB; git checkout -- . ; git clean -fdq; Pop-Location
    Push-Location $wbDir; git checkout -- . ; git clean -fdq; Pop-Location
    Section 'done'
    Write-Host ("A {0} (+{1} verify)   B {2}   C {3}   credits; transcripts in kit\results\eval" -f $cpA.credits, $verifyCredits, $cpB.credits, $cpC.credits)
  }
  'clean' {
    foreach ($r in @((Join-Path $Bench 'full-repo'), $ArmB)) {
      $p = Join-Path $r $specRel
      if (Test-Path $p) { Remove-Item $p; Write-Host "removed $p" }
    }
  }
}
