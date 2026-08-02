# Typeset the UncertaiNLP short paper with TinyTeX.
#
# `acl.sty` and `acl_natbib.bst` are NOT vendored — the upstream repository declares no licence, so
# we have no redistribution right (docs/writeup/acl-template.md records the pinned fetch). They are
# found via TEXINPUTS/BSTINPUTS pointing at the gitignored docs/writeup/acl-template/ instead of
# being copied into the tree, so nothing unlicensed can be committed by accident.
#
# Run from the repository root:  pwsh -File scripts/build_paper.ps1

$ErrorActionPreference = 'Stop'

$root     = Split-Path -Parent $PSScriptRoot
$writeup  = Join-Path $root 'docs\writeup'
$template = Join-Path $writeup 'acl-template'
$texbin   = Join-Path $env:APPDATA 'TinyTeX\bin\windows'
$stem     = 'uncertainlp-2026-short'

if (-not (Test-Path (Join-Path $template 'acl.sty'))) {
    throw "acl.sty is missing from $template. It is deliberately not committed; fetch it with the pinned command in docs/writeup/acl-template.md."
}
if (-not (Test-Path (Join-Path $texbin 'pdflatex.exe'))) {
    throw "No TinyTeX at $texbin. Install it, or point `$texbin at another TeX distribution."
}

$env:PATH       = "$texbin;$env:PATH"
# Trailing ';' means "and also the default search path" — without it TeX finds none of its own files.
$env:TEXINPUTS  = ".;$template;"
$env:BSTINPUTS  = ".;$template;"
$env:BIBINPUTS  = ".;$template;"

Push-Location $writeup
try {
    # pdflatex, bibtex, pdflatex x2 — the standard dance that resolves \cite and \ref cross-references.
    & pdflatex -interaction=nonstopmode -file-line-error $stem | Out-Null
    & bibtex $stem | Out-Null
    & pdflatex -interaction=nonstopmode -file-line-error $stem | Out-Null
    $final = & pdflatex -interaction=nonstopmode -file-line-error $stem

    $errors = $final | Select-String -Pattern '^!|:\d+:.*Error'
    if ($errors) {
        $errors | Select-Object -First 20 | ForEach-Object { $_.Line }
        throw 'LaTeX reported errors; see above and docs/writeup/uncertainlp-2026-short.log.'
    }

    $pages = ($final | Select-String -Pattern 'Output written on .*\((\d+) pages').Matches.Groups[1].Value
    $undef = $final | Select-String -Pattern 'Warning: (Citation|Reference).*undefined'
    "built  : $writeup\$stem.pdf"
    "pages  : $pages"
    if ($undef) {
        'WARNING: undefined citations or references remain:'
        $undef | Select-Object -First 10 | ForEach-Object { "  " + $_.Line.Trim() }
    } else {
        'refs   : all citations and cross-references resolved'
    }
    if ([int]$pages -gt 5) {
        "NOTE: $pages pages. ACL short papers allow 4 pages of content; Limitations and References"
        '      do not count toward it, so check where the content actually ends before cutting.'
    }
}
finally {
    Pop-Location
}
