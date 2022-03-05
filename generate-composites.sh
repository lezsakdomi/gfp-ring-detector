files="$(find "képek/" -name "*_c0.tif")"
count="$(echo "$files" | wc -l)"
i=0
echo "$files" | while IFS= read file; do
  let i++
  printf "$i / $count\r"
  folder="$(dirname "$file")"
  convert "$folder"/*_c1.tif "$folder"/*_c2.tif "$folder"/*_c0.tif -combine "$folder"/composite.tif
  convert "$folder"/composite.tif "$folder"/composite.jpg
done
echo
