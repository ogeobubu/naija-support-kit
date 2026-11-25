#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

attempts="${PULL_ATTEMPTS:-5}"
delay="${PULL_RETRY_DELAY:-10}"
if [[ ! "$attempts" =~ ^[1-9][0-9]*$ || ! "$delay" =~ ^[0-9]+$ ]]; then
  printf 'PULL_ATTEMPTS must be positive; PULL_RETRY_DELAY must be nonnegative.\n' >&2
  exit 2
fi

services=(postgres redis mailpit rails)
if (( $# )); then
  services=("$@")
fi

for service in "${services[@]}"; do
  succeeded=false
  for (( attempt=1; attempt<=attempts; attempt++ )); do
    printf '\nDownloading %s image (attempt %s/%s)...\n' "$service" "$attempt" "$attempts"
    if docker-compose --parallel 1 pull --policy missing "$service"; then
      succeeded=true
      break
    fi
    if (( attempt < attempts )); then
      printf 'Pull failed. Waiting %s seconds before retrying %s.\n' "$delay" "$service" >&2
      sleep "$delay"
    fi
  done
  if [[ "$succeeded" != true ]]; then
    printf '\nCould not download %s after %s attempts. Startup stopped.\n' "$service" "$attempts" >&2
    printf 'Completed images remain cached. Retry: bash scripts/start.sh\n' >&2
    exit 1
  fi
done
