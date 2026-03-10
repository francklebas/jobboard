#!/bin/bash

# ============================================================
# VueJobs scraper — toutes les offres remote
# Usage: ./vuejobs_scrape.sh
# Remplace les valeurs COOKIE_SESSION et COOKIE_XSRF
# ============================================================

COOKIE_SESSION="eyJpdiI6ImpIVDVrVHkvempBTTIwTmVwVDVxd0E9PSIsInZhbHVlIjoiTVJUV1YrcXJVbmtTWEJJN2RYWjFIWDdYYlJrOEg2WW5pblNyNVk1Si9FVytQa2FTYnR6MU1hTEozelFyWEdraHZCU1gwNjkrdmdJSzMrb0JlVzdRVmxoZUt0NHNaeDVJWUZESitVK1hvR0ZTOGpkUUJCY25BNTRBN1RTRWx1MU8iLCJtYWMiOiJiMWM0ZDlmMmFmMDZmMDM0NWFlMjBiOGY0NGIzZTlkOTRlZjhlNGYwOTVhZTFkMzM0ZWQ5MGRlYTBkODNkMDQ2IiwidGFnIjoiIn0%3D"       # valeur de vue_jobs_...
COOKIE_XSRF="eyJpdiI6IklsTXdMeGlqM3hSSDBIa2hSdWVDZkE9PSIsInZhbHVlIjoiUU91U05reEhVVGFrRkNXWHFyc3VWVE5hckpHUVQyTVFVb1diclhKeW1uZ21SMEtCdGZzQm5YakE3OHVjYk9nM1VydTlvYUUzZWxIR0dRK0RnQVEyNG1zTGpUNjZPLy9PWkpPN2ZMMVpNTGhBam1OY1lFMTJrc2dkRGlPS1dQd08iLCJtYWMiOiIzZjZkZWMwZjliMTY5NzliMGZhZTI4ZDNiMzJjYjc4NWNmN2NmZTBlOWZlOWRiYTRjNTYyMTYzMWEwYWQ5ZTBmIiwidGFnIjoiIn0%3D"          # valeur de XSRF-TOKEN
COOKIE_SESSION_NAME="vue_jobs_session"  # nom exact du cookie (vérifie dans devtools)
XSRF_NAME="XSRF-TOKEN"

BASE_URL="https://app.vuejobs.com/posts/open"
PARAMS="top=true&filter%5Bwork_place%5D=remote&filter%5Bseniority%5D=mid-level&sort=-published_at"
OUTPUT_FILE="vuejobs_all.json"
TOTAL_PAGES=9  # ajuste si nécessaire

echo "[]" > "$OUTPUT_FILE"

for page in $(seq 1 $TOTAL_PAGES); do
  echo "→ Page $page..."

  RESPONSE=$(curl -s \
    "${BASE_URL}?${PARAMS}&page=${page}" \
    -H "Accept: application/json" \
    -H "X-XSRF-TOKEN: ${COOKIE_XSRF}" \
    -H "Cookie: ${COOKIE_SESSION_NAME}=${COOKIE_SESSION}; ${XSRF_NAME}=${COOKIE_XSRF}" \
    -H "Referer: https://app.vuejobs.com/" \
    -H "User-Agent: Mozilla/5.0")

  # Merge dans le fichier output
  echo "$RESPONSE" | jq --argjson existing "$(cat $OUTPUT_FILE)" \
    '$existing + .data' > tmp_merge.json && mv tmp_merge.json "$OUTPUT_FILE"

  sleep 1  # sois poli
done

echo ""
echo "✓ Done. $(cat $OUTPUT_FILE | jq length) offres dans $OUTPUT_FILE"

# Affichage lisible
echo ""
echo "=== OFFRES ==="
cat "$OUTPUT_FILE" | jq -r '.[] | "[\(.seniority // "?")] \(.title) — \(.locations[0].country // "remote") | \(.slug)"'
