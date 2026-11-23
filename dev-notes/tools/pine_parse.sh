#!/bin/bash
# usage: pine_parse.sh FILE [BASELINE_FILE]
# Syntax-parses every top-level statement of FILE with pynescript (or only those that differ from BASELINE_FILE).
# Prints one line per chunk (OK/FAIL with the source line number) and a summary.
T=$(cd "$(dirname "$0")" && pwd); SP=$(dirname "$T")
W=$(mktemp -d "$SP/runs/parse.XXXXXX" 2>/dev/null || (mkdir -p "$SP/runs" && mktemp -d "$SP/runs/parse.XXXXXX"))
"$SP/venv/bin/python" -I "$T/split.py" "$1" "$W/new" > /dev/null
if [ -n "$2" ]; then
  "$SP/venv/bin/python" -I "$T/split.py" "$2" "$W/old" > /dev/null
  (cd "$W/old" && md5sum *.pine | awk '{print $1}' | sort -u) > "$W/old.md5"
  for f in "$W"/new/*.pine; do h=$(md5sum "$f" | awk '{print $1}'); grep -q "^$h$" "$W/old.md5" || echo "$f"; done > "$W/todo"
else
  ls "$W"/new/*.pine > "$W/todo"
fi
N=$(wc -l < "$W/todo")
cat "$W/todo" | xargs -P 2 -I{} sh -c 'r=$(timeout 1200 "'"$SP"'/venv/bin/python" -I "'"$T"'/parse_one.py" "{}" 2>&1 | tail -1); b=$(basename "{}" .pine); if echo "$r" | grep -q "parsed OK"; then echo "OK $b"; else echo "FAIL $b :: $r"; fi' | sort
echo "SUMMARY: $(grep -c . "$W/todo") chunks checked; see FAIL lines above (none = all parsed)"
