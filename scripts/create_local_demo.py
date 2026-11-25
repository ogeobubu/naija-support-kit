"""Create an isolated fictional Website inbox and configure the local connector."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', type=int, required=True)
    args = parser.parse_args()
    if args.account < 1:
        parser.error('account must be a positive ID')
    result = subprocess.run(
        ['docker-compose', 'exec', '-T', '-e', f'LOCAL_DEMO_ACCOUNT_ID={args.account}',
         'rails', 'bundle', 'exec', 'rails', 'runner', '-'],
        input=(ROOT / 'scripts/create_local_demo.rb').read_text(),
        capture_output=True, text=True, cwd=ROOT
    )
    marker = 'LOCAL_DEMO_RESULT='
    payload = next((line[len(marker):] for line in result.stdout.splitlines() if line.startswith(marker)), None)
    if result.returncode or not payload:
        # No token is written by the Ruby script until the transaction succeeds.
        print('Demo setup failed. Rails error:', file=sys.stderr)
        print(result.stderr[-4000:], file=sys.stderr)
        return 1
    details = json.loads(payload)
    token = details.pop('api_token')
    env_file = ROOT / '.env'
    updates = {'CHATWOOT_ACCOUNT_ID': str(details['account_id']),
               'CHATWOOT_INBOX_ID': str(details['inbox_id']),
               'CHATWOOT_API_TOKEN': token}
    lines = env_file.read_text().splitlines()
    found = set()
    for index, line in enumerate(lines):
        key = line.split('=', 1)[0]
        if key in updates:
            lines[index] = key + '=' + updates[key]
            found.add(key)
    lines.extend(key + '=' + value for key, value in updates.items() if key not in found)
    env_file.write_text('\n'.join(lines) + '\n')
    env_file.chmod(0o600)
    details['widget_url'] = 'http://localhost:3000/widget?website_token=' + details['website_token']
    path = ROOT / 'data/local-demo.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(details, indent=2) + '\n')
    print(f"Demo inbox ready: account {details['account_id']}, inbox {details['inbox_id']}.")
    print('Connector token saved privately in .env; existing user credentials were not changed.')
    print('Recreate the connector: docker-compose up -d --force-recreate bot')
    print('Public widget URL:', details['widget_url'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
