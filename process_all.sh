#!/bin/bash
find 'test-images/' -name 'stats.txt' -delete
folders="$(find 'test-images/' -name '*_Files' -type d)"
count=$(echo "$folders" | wc -l)

main(){
  i=0
  echo "$folders" | while IFS= read folder; do
    let i++
    if [ $# -eq 2 ] && [ "$(( i % $1 ))" -ne "$(( $2 % $1 ))" ]; then
      continue
    fi
    echo "\e[1m[$i / $count] $folder\e[0m"
    fn="$(find "$folder/" -name '*_c0.tif' | head -n1)"

    handle_output(){
      if [ -z "$SILENT" ]; then
        tee -a "$folder"/stats.log
        echo
      else
        cat >"$folder"/stats.log
      fi
    }

    python pipeline.py "${fn%_c0.tif}_c{}.tif" "$folder" 2>&1 | handle_output \
      && echo "$folder" >> done.txt
  done
}

case $# in
  0)
    rm done.txt
    main
    ;;

  1)
    rm done.txt
    NUM_THREADS=$1
    for i in {1..$NUM_THREADS}; do
      SILENT=1 main $NUM_THREADS $i &
    done

    stop() {
      printf '\n%s\n' "received SIGINT, killing child processes"
      kill -KILL ${${(v)jobstates##*:*:}%=*}
    }
    trap stop SIGINT

    wait
    ;;

  2)
    main "$1" "$2"
    ;;

  *)
    echo "Usage: $0 [num_threads] [thread_id]"
    exit 1
esac