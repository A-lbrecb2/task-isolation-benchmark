#!/usr/bin/env bash
# Installs dependencies for the full repository and every slice.
set -e
cd "$(dirname "$0")"
for d in full-repo slices/*/; do
  echo "== npm install in $d"
  (cd "$d" && npm install --legacy-peer-deps --no-audit --no-fund)
done
echo "done. Next: ./test.sh full-repo"
