# AutoWebUI one-click installer (Windows)
# Usage: extract, cd into AutoWebUI, run: .\install.ps1   (add -SkipBuild to skip index build)
# NOTE: keep ASCII-only (PS 5.1 parses .ps1 without BOM as GBK)
param([switch]$SkipBuild)
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot

Write-Host '=== AutoWebUI install ==='

# 1) Python + numpy
Write-Host '[1/4] checking Python / numpy'
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
  Write-Host '[!] python not found. Install Python 3.11+ from https://www.python.org/downloads/ (check "Add to PATH")'
  exit 1
}
python -c "import numpy" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host '     installing numpy ...'
  $env:TMP = "$here\.tmp"; $env:TEMP = "$here\.tmp"
  New-Item -ItemType Directory -Force "$here\.tmp" | Out-Null
  python -m pip install -q numpy 2>$null
  if ($LASTEXITCODE -ne 0) { python -m pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple numpy }
  python -c "import numpy" 2>$null
  if ($LASTEXITCODE -ne 0) { Write-Host '[!] numpy install failed, run manually: pip install numpy'; exit 1 }
}

# 2) config
Write-Host '[2/4] generating config.json'
if (-not (Test-Path "$here\config.json")) {
  Copy-Item "$here\config.example.json" "$here\config.json"
  Write-Host '     created config.json - edit if WebUI/embedding URLs or Anima CLIP/VAE paths differ, then re-run'
}

# 3) env detect
Write-Host '[3/4] environment detection'
python "$here\setup\detect_env.py"

# 4) tag index
Write-Host '[4/4] building Danbooru tag index (needs embedding service; use -SkipBuild to skip)'
if (-not $SkipBuild) {
  python "$here\tagsearch\build_index.py"
  if ($LASTEXITCODE -ne 0) {
    Write-Host '     [i] index build incomplete (embedding service not ready? later run: python tagsearch\build_index.py)'
  }
}

Write-Host ''
Write-Host '=== install done, next steps ==='
Write-Host '  1) import settings/novels: put files into import/ then run  python settings_rag\import_docs.py'
Write-Host '  2) full init guide:         read setup\README.md'
Write-Host '  3) generate illustration:   python pipeline\generate.py --help'
Write-Host '  4) daily workflows:         see WORKFLOWS.md'
