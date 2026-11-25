"""Audit the Git index for private runtime files and obvious exposed credentials."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DOCS = {'docs/first-customer-plan.md', 'docs/pilot-offer.md', 'docs/prospect-shortlist.md'}
PATTERNS = [
    (re.compile(r'gh[opusr]_[A-Za-z0-9_]{20,}'), 'GitHub credential pattern'),
    (re.compile(r'AKIA[A-Z0-9]{16}'), 'AWS credential pattern'),
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'), 'private key'),
    (re.compile(r'/Users/[A-Za-z0-9_.-]+/'), 'personal macOS path'),
    (re.compile(r'website_token=[A-Za-z0-9]{16,}'), 'literal local widget token'),
]


def main():
    result = subprocess.run(['git', 'ls-files', '--cached', '-z'], cwd=ROOT, capture_output=True)
    if result.returncode:
        print('Run this check inside an initialized Git repository after staging files.')
        return 2
    paths = [p for p in result.stdout.decode().split('\0') if p]
    if not paths:
        print('No staged or tracked files to inspect.')
        return 2
    secrets = []
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if '=' not in line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            if len(value) >= 12 and any(term in key for term in ('SECRET', 'PASSWORD', 'TOKEN')):
                secrets.append(value)
    problems = []
    for path in paths:
        parts = Path(path).parts
        name = Path(path).name
        if (parts[0] in {'data', 'sales', '.aws', '.secrets', '.codex'} or path in PRIVATE_DOCS
                or (name.startswith('.env') and path != '.env.example')
                or name.endswith(('.sqlite', '.sqlite3', '.log', '.pem', '.key'))):
            problems.append((path, 'private or runtime file'))
        content = subprocess.run(['git', 'show', ':' + path], cwd=ROOT, capture_output=True, check=True).stdout.decode(errors='replace')
        for pattern, reason in PATTERNS:
            if pattern.search(content):
                problems.append((path, reason))
        if any(secret in content for secret in secrets):
            problems.append((path, 'value from local secret configuration'))
    if problems:
        for path, reason in problems:
            print(f'FAIL {path}: {reason}')
        print('Credential values are deliberately not printed.')
        return 1
    print(f'PASS: audited {len(paths)} indexed files; no forbidden files or matching credential patterns.')
    print('This bounded check supplements manual review; it is not a complete secret scanner.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
