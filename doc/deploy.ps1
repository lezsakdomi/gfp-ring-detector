Push-Location $PSScriptRoot

Remove-Item -Recurse -ErrorAction SilentlyContinue .\plantuml-images\
Remove-Item -Recurse -ErrorAction SilentlyContinue .\dist-windows\
Remove-Item -ErrorAction SilentlyContinue doc.prep.md

& wsl export GITHUB_REF_NAME=local GITHUB_ACTION_REPOSITORY=lezsakdomi/gfp-ring-detector GITHUB_SHA=master ';' `
    liquid '<doc.md' '>doc.prep.md' '"$(jq -n env)"'
& wsl export 'PATH="$PATH:/home/led/.local/bin/"' ';' `
    pandoc -o doc.html doc.prep.md --filter pandoc-plantuml

New-Item -Type Directory -ErrorAction SilentlyContinue -Name dist-windows
Copy-Item -Path ..\dist\gfp-ring-detector.exe -Destination .\dist-windows\

git add index.html doc.html plantuml-images dist-windows/gfp-ring-detector.exe
git commit --amend -m "Basic documentation"
git push --force origin gh-pages

Pop-Location
