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

  Options: -NoPolicy (round-1 style guardrails, no Policy section, no SBOM baseline)
           -Bench <path> (default C:\Crodox\task-isolation-benchmark)
           -ArmB  <path> (default C:\Crodox\armB-full-repo)

  Run from PowerShell 7. Needs python on PATH. Does not touch the Codespace; arm C is evaluated
  from a local clone so that no kit file ever enters the workbench.
#>
param(
  [Parameter(Mandatory = $true, Position = 0)][ValidateSet('reset', 'eval', 'evalc', 'clean')][string]$Phase,
  [Parameter(Mandatory = $true, Position = 1)][string]$Task,
  [Parameter(Position = 2)][string]$WorkbenchUrl,
  [string]$Bench = 'C:\Crodox\task-isolation-benchmark',
  [string]$ArmB = 'C:\Crodox\armB-full-repo',
  [switch]$NoPolicy
)
$ErrorActionPreference = 'Stop'
$kit = Join-Path $Bench 'kit'
$tasks = (Get-Content (Join-Path $kit 'tasks.json') -Raw | ConvertFrom-Json).tasks
$t = $tasks | Where-Object { $_.id -eq $Task }
if (-not $t) { throw "unknown task $Task" }
$specSrc = Join-Path $kit $t.spec_file
$specRel = $t.spec_target_path -replace '/', '\'
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$evalDir = Join-Path $kit 'results\eval'
New-Item -ItemType Directory -Force -Path $evalDir | Out-Null

function Section($txt) { Write-Host "`n== $txt ==" -ForegroundColor Cyan }

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
  'clean' {
    foreach ($r in @((Join-Path $Bench 'full-repo'), $ArmB)) {
      $p = Join-Path $r $specRel
      if (Test-Path $p) { Remove-Item $p; Write-Host "removed $p" }
    }
  }
}
