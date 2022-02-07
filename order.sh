STREAM="$1"

mkdir ordered || rm ordered/*.tif

if [ -z "$STREAM" ]; then
  files="$(find "képek/" -name "stats.txt")"
  count="$(echo "$files" | wc -l)"
else
  count="?"
fi

i=0

if [ -z "$STREAM" ]; then
  echo "$files"
else
  cat "$STREAM"
fi | while IFS= read file; do
  let i++
  printf "$i / $count\r"
  if [ -z "$STREAM" ]; then
    folder="../$(dirname "$file")"
  else
    folder="$file"
    file="$folder/stats.txt"
  fi

  if [ $(cat "$file" | wc -l) -lt 2 ]; then
    echo "Warning: $file is invalid - skipping"
    continue
  fi
  linkname="ordered/$(cat "$file" | head -n1)-$(basename "$folder").tif"
   ln -s "$folder/composite.tif" "$linkname"
  # convert "$folder"/*_c?.tif -combine "$linkname"
done
echo
