mkdir ordered || rm ordered/*.tif
files="$(find "képek/" -name "stats.txt")"
count="$(echo "$files" | wc -l)"
i=0
echo "$files" | while IFS= read file; do
  let i++
  printf "$i / $count\r"
  folder="../$(dirname "$file")"
  if [ $(cat "$file" | wc -l) -lt 2 ]; then
    echo "Warning: $file is invalid - skipping"
    continue
  fi
  linkname="ordered/$(cat "$file" | head -n1)-$(basename "$folder").tif"
   ln -s "$folder/composite.tif" "$linkname"
  # convert "$folder"/*_c?.tif -combine "$linkname"
done
echo
