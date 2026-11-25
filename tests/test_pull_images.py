"""Exercise retry and stop behavior with a fake Compose executable."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImagePullTests(unittest.TestCase):
    def run_pull(self, failures, *services, attempts='3'):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder)
            fake = temp / 'docker-compose'
            fake.write_text('''#!/usr/bin/env bash
set -eu
count=0
if [[ -f "$PULL_TEST_COUNT" ]]; then read -r count < "$PULL_TEST_COUNT"; fi
count=$((count+1))
printf '%s\\n' "$count" > "$PULL_TEST_COUNT"
printf '%s\\n' "$*" >> "$PULL_TEST_LOG"
if (( count <= PULL_TEST_FAILURES )); then
  printf 'simulated TLS handshake timeout\\n' >&2
  exit 1
fi
''')
            fake.chmod(0o700)
            env = dict(os.environ, PATH=folder + os.pathsep + os.environ['PATH'],
                       PULL_TEST_COUNT=str(temp / 'count'), PULL_TEST_LOG=str(temp / 'log'),
                       PULL_TEST_FAILURES=str(failures), PULL_ATTEMPTS=attempts, PULL_RETRY_DELAY='0')
            result = subprocess.run(['bash', str(ROOT / 'scripts/pull-images.sh'), *services],
                                    env=env, text=True, capture_output=True, timeout=10)
            log = (temp / 'log').read_text().splitlines() if (temp / 'log').exists() else []
            return result, log

    def test_recovers_then_moves_to_next_service(self):
        result, log = self.run_pull(2, 'postgres', 'redis')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log, ['--parallel 1 pull --policy missing postgres'] * 3 +
                         ['--parallel 1 pull --policy missing redis'])

    def test_exhausted_retries_stop_before_next_service(self):
        result, log = self.run_pull(10, 'postgres', 'redis')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(log), 3)
        self.assertFalse(any('redis' in line for line in log))
        self.assertIn('Startup stopped', result.stderr)

    def test_rejects_zero_attempts_before_pulling(self):
        result, log = self.run_pull(0, 'postgres', attempts='0')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(log, [])


if __name__ == '__main__':
    unittest.main()
