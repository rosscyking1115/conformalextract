# Typeset the UncertaiNLP short paper with TinyTeX.
#
# `acl.sty` and `acl_natbib.bst` are NOT vendored — the upstream repository declares no licence, so
# we have no redistribution right (docs/writeup/acl-template.md records the pinned fetch). They are
# found via TEXINPUTS/BSTINPUTS pointing at the gitignored docs/writeup/acl-template/ instead of
# being copied into the tree, so nothing unlicensed can be committed by accident.
#
# Run from the repository root:  pwsh -File scripts/build_paper.ps1

param([switch]$SelfTest, [switch]$Bylined)

$ErrorActionPreference = 'Stop'

# LaTeX resolves \ref and \cite by writing them to .aux on one pass and reading them back on the
# next, so a build can emit a PDF whose cross-references are a pass out of date. It says so — and
# only in this warning. The previous version of this script grepped for UNDEFINED references, which
# is a different condition: an undefined ref never resolved at all, an unsettled one resolved to a
# stale value. A build one pass short reports "all citations and cross-references resolved" and
# ships wrong numbers. That is this project's own defect class — a gate checking the wrong property
# and returning ok — so the check is on the warning itself, and running short of passes is fatal.
function Test-CrossReferencesUnsettled {
    param([string[]]$Output)
    [bool]($Output | Select-String -Pattern 'Rerun to get cross-references right|Label\(s\) may have changed')
}

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
    if ($Bylined) {
        # The WRITING-SAMPLE variant: bylined, no line numbers, no "Anonymous ACL submission".
        # DERIVED from the submission source by substitution rather than maintained as a second
        # copy, because a second copy of a paper is exactly the drift this repository has already
        # been bitten by - docs/writeup/uncertainlp-2026-short.md records a Markdown duplicate that
        # was deleted rather than updated for the same reason. The submission .tex is not touched.
        $sourceTex  = "$stem.tex"
        $bylinedStem = "$stem-bylined"
        $body = Get-Content $sourceTex -Raw

        $anonPkg = '\usepackage[review]{acl}'
        $anonAuth = '\author{Anonymous submission}'
        if ($body -notmatch [regex]::Escape($anonPkg)) { throw "Expected '$anonPkg' in $sourceTex; the variant's substitution is stale." }
        if ($body -notmatch [regex]::Escape($anonAuth)) { throw "Expected '$anonAuth' in $sourceTex; the variant's substitution is stale." }

        $body = $body.Replace($anonPkg, '\usepackage{acl}')
        $body = $body.Replace($anonAuth, '\author{Cheng-Yuan King \\ \texttt{rosscyking1115@gmail.com}}')
        Set-Content -Path "$bylinedStem.tex" -Value $body -NoNewline -Encoding utf8
        $stem = $bylinedStem
        "variant: bylined writing sample (submission .tex untouched)"
    }

    if ($SelfTest) {
        # Both directions, against the real toolchain. A check nobody has watched fail is a check
        # nobody has evidence for, which is the same absence this repository keeps finding.
        foreach ($e in @('aux','log','out','blg','bbl')) {
            $f = "$stem.$e"; if (Test-Path $f) { Remove-Item $f -Force }
        }
        # MUST-FAIL: one pass from a cold .aux cannot have settled anything.
        $one = & pdflatex -interaction=nonstopmode -file-line-error $stem
        if (-not (Test-CrossReferencesUnsettled $one)) {
            throw 'SELFTEST FAILED (must-fail direction): a single cold pass was not detected as unsettled.'
        }
        'selftest: unsettled build correctly DETECTED after 1 pass'
        # MUST-PASS: the full dance below must settle. Fall through and let it run.
    }

    # pdflatex, bibtex, pdflatex x2 — the standard dance that resolves \cite and \ref cross-references.
    & pdflatex -interaction=nonstopmode -file-line-error $stem | Out-Null
    # bibtex's output was discarded here until 2026-08-09, and that hid a broken bibliography: a
    # malformed entry produced empty author/year/booktitle and rendered "[hua()]", yet pdflatex
    # still reported every citation RESOLVED, because a \bibitem existed - it just said nothing.
    # An undefined-citation check cannot see a citation that resolves to garbage.
    $bib = & bibtex $stem 2>&1
    $bibBad = $bib | Select-String -Pattern "^Warning--(empty|to sort, need)|I couldn't open|error message"
    if ($bibBad) {
        $bibBad | Select-Object -First 10 | ForEach-Object { "  " + $_.Line.Trim() }
        throw 'bibtex reported errors or empty fields; the bibliography is wrong even if citations "resolve".'
    }
    & pdflatex -interaction=nonstopmode -file-line-error $stem | Out-Null
    $final = & pdflatex -interaction=nonstopmode -file-line-error $stem

    # The three-pass dance is not always enough — it was not on 2026-08-09, when a clean build
    # shipped with this warning still standing and the script reported success. Rerun while the
    # warning persists, then treat a still-unsettled build as fatal rather than as a note.
    $extra = 0
    while ((Test-CrossReferencesUnsettled $final) -and $extra -lt 3) {
        $extra++
        "rerun  : cross-references unsettled, pass $($extra + 3)"
        $final = & pdflatex -interaction=nonstopmode -file-line-error $stem
    }
    if (Test-CrossReferencesUnsettled $final) {
        throw "Cross-references still unsettled after $($extra + 3) passes. The PDF's \ref and \cite values are a pass out of date; do not use it."
    }
    if ($SelfTest) { 'selftest: settled build correctly ACCEPTED' }

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
    # The limit is the venue's, read from https://uncertainlp.github.io/ on 2026-08-03: full
    # papers up to 8 pages, short up to 4. THIS PAPER TARGETS THE FULL FORMAT. The number lived
    # for weeks as an untraced assumption in reviewer_analysis.md and three factual defects came
    # out of compressing to it, so the source is named here rather than the number repeated.
    if ([int]$pages -gt 9) {
        "NOTE: $pages pages. UncertaiNLP full papers allow 8 pages of CONTENT; Limitations,"
        '      References and appendices do not count, so measure where the content actually'
        '      ends (from this build, never from a stored figure) before cutting anything.'
    }
}
finally {
    Pop-Location
}
