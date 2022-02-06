files="$(find "képek/" -name "*_c0.tif")"
count="$(echo "$files" | wc -l)"
i=0
echo "$files" | while IFS= read file; do
  let i++
  printf "$i / $count\r"
  folder="$(dirname "$file")"
  convert "$folder"/*_c?.tif -combine "$folder"/composite.tif
done
echo
