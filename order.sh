STREAM="$1"

if [ -z "$NO_RM" ]; then
  mkdir ordered || rm ordered/* || :
  [ -z "$ZIP_FILE" ] || rm "$ZIP_FILE"
fi

if [ -z "$STREAM" ]; then
  files="$(find "képek/" -name "stats.txt" -newer "képek/2021-07-15_GlueRab7_ctrl_-2h/GlueRab7_ctrl_-2h-0018.tif_Files/stats.txt")"
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
  if [ -z "$STREAM" ]; then
    folder="../$(dirname "$file")"
  else
    folder="$file"
    file="$folder/stats.txt"
  fi
  
  if [ -n "$NO_RM" ]; then
    if [ -n "$(find ordered/ -name "*-$(basename "$folder")" -maxdepth 1 -print -quit)" ]; then
      continue
    fi
  fi

  printf "$i / $count\r"

  if [ $(cat "$file" | wc -l) -lt 2 ]; then
    echo "Warning: $file is invalid - skipping"
    continue
  fi
  linkname="ordered/$(cat "$file" | grep -oP 'Scalar positives: \K.*')-$(basename "$folder")"
   ln -s "$folder/composite.tif" "$linkname.tif"
   ln -s "$folder" "$linkname"
  # convert "$folder"/*_c?.tif -combine "$linkname"
done
echo
if [ -n "$ZIP_FILE" ]; then
  zip ${NO_RM:+-u} "$ZIP_FILE" ordered/*/composite.jpg ordered/*/*.txt
  du -h "$ZIP_FILE"
fi