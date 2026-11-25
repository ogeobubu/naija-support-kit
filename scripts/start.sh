#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

missing=()
for tool in colima docker docker-compose; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    missing+=("$tool")
  fi
done
if (( ${#missing[@]} )); then
  printf 'Missing tools: %s\n' "${missing[*]}"
  printf 'Install them first, and wait for installation to finish:\n'
  printf '  HOMEBREW_NO_AUTO_UPDATE=1 brew install colima docker docker-compose docker-buildx\n'
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  printf 'Docker Buildx is missing or Docker cannot find its plugin.\n' >&2
  printf 'Install it with: brew install docker-buildx\n' >&2
  printf 'Register Homebrew plugins using the instructions in README.md.\n' >&2
  exit 1
fi

python3 scripts/setup.py
if ! docker info >/dev/null 2>&1; then
  colima start --cpu 4 --memory 6 --disk 40
fi
docker-compose config --quiet
bash scripts/pull-images.sh
docker-compose build bot
docker-compose run --rm rails bundle exec rails db:chatwoot_prepare
docker-compose up -d
printf '\nChatwoot is starting: http://localhost:3000\n'
printf 'Check readiness with: docker-compose logs --tail=50 rails\n'
