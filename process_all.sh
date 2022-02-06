#!/bin/zsh
find 'képek/' -name 'stats.txt' -delete
folders="$(find 'képek/' -name '*_Files')"
count=$(echo "$folders" | wc -l)
i=0
echo "$folders" | while IFS= read folder; do
  let i++
  if [ $# -eq 2 -a "$(( i % $1 ))" -ne "$(( $2 % $1 ))" ]; then
    continue
  fi
  echo "\e[1m[$i / $count] $folder\e[0m"
  fn="$(find "$folder/" -name '*_c0.tif' | head -n1)"
  time python pipeline.py "${fn%_c0.tif}_c{}.tif" "$folder" >"$folder/stats.txt"
  echo
done