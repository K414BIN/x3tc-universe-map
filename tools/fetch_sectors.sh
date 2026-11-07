#!/usr/bin/env bash
# Fetch all X3:TC universe sector pages from x3tc.net into sectors/
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/sectors"
CODES="$ROOT/data/codes.txt"
mkdir -p "$OUT" "$ROOT/data"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

while read -r code; do
  [ -z "$code" ] && continue
  f="$OUT/$code.html"
  if [ -s "$f" ] && [ "$(stat -c %s "$f")" -gt 2000 ]; then continue; fi
  curl -s -4 --compressed --max-time 25 --retry 2 \
    -A "$UA" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    -H "Accept-Language: ru-RU,ru;q=0.9" \
    -H "Referer: https://x3tc.net/x3_tc_map/" \
    "https://x3tc.net/x3_tc_map/sector.php?c=$code" -o "$f"
  sz=$(stat -c %s "$f" 2>/dev/null || echo 0)
  if [ "$sz" -lt 2000 ]; then echo "FAIL $code size=$sz"; fi
done < "$CODES"
echo "DONE $(ls "$OUT" | wc -l) files"
