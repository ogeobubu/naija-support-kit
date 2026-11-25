#!/usr/bin/env bash
set -u

missing=0
for tool in colima docker docker-compose; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'Installed: %s\n' "$tool"
  else
    printf 'Not installed yet: %s\n' "$tool"
    missing=1
  fi
done

if (( missing == 0 )); then
  printf '\nReady. Start Chatwoot with: bash scripts/start.sh\n'
elif pgrep -f '[b]rew.rb install colima docker docker-compose' >/dev/null 2>&1; then
  printf '\nHomebrew installation is still running. Wait for it to finish.\n'
  printf 'Do not start another installation while this one is running.\n'
else
  printf '\nNo matching installation is running. Install the missing tools with:\n'
  printf 'HOMEBREW_NO_AUTO_UPDATE=1 brew install colima docker docker-compose\n'
fi
