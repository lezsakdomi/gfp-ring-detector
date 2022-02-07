folder="$(wmctrl -l|awk '{$3=""; $2=""; $1=""; print $0}' | grep -oP 'feh \[\d+ of \d+\] - \K.*_Files' || exit 1)"
fn="$(find "$folder/" -name '*_c0.tif' | head -n1)"
echo "Found $fn"
python pipeline.py "${fn%_c0.tif}_c{}.tif"