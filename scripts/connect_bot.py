"""Attach the local pilot bot to an existing Chatwoot inbox."""
import argparse
from getpass import getpass
import json
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
env_path = root / '.env'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--account', required=True, type=int)
    parser.add_argument('--inbox', required=True, type=int)
    parser.add_argument('--url', default='http://localhost:3000')
    args = parser.parse_args()
    lines = env_path.read_text().splitlines()
    env = dict(line.split('=', 1) for line in lines if line and not line.startswith('#') and '=' in line)
    token = getpass('Chatwoot administrator API token (hidden): ').strip()
    if not token:
        raise SystemExit('A token is required.')

    def api(path, body=None):
        req = Request(args.url.rstrip('/') + f'/api/v1/accounts/{args.account}' + path,
                      data=None if body is None else json.dumps(body).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with urlopen(req, timeout=20) as response:
            content = response.read()
            return json.loads(content) if content else None

    inbox = api(f'/inboxes/{args.inbox}')
    if inbox.get('id') != args.inbox:
        raise SystemExit('Inbox could not be verified.')
    bots = api('/agent_bots')
    if isinstance(bots, dict):
        bots = bots.get('payload', bots.get('data', []))
    name = f'Local FAQ pilot inbox {args.inbox}'
    existing = next((b for b in bots if b.get('name') == name), None)
    outgoing_url = 'http://bot:8080/webhook/' + env['BOT_WEBHOOK_SECRET']
    if existing:
        if existing.get('outgoing_url') != outgoing_url:
            raise SystemExit('Existing pilot bot has a different URL. Review it in Chatwoot first.')
        created = existing
    else:
        created = api('/agent_bots', {'name': name, 'description': 'Approved FAQ answers and human handoff', 'outgoing_url': outgoing_url, 'bot_type': 0})
    api(f'/inboxes/{args.inbox}/set_agent_bot', {'agent_bot': created['id']})
    replacements = {'CHATWOOT_ACCOUNT_ID': str(args.account), 'CHATWOOT_INBOX_ID': str(args.inbox), 'CHATWOOT_API_TOKEN': token}
    env_path.write_text('\n'.join(
        line.split('=', 1)[0] + '=' + replacements[line.split('=', 1)[0]]
        if '=' in line and line.split('=', 1)[0] in replacements else line
        for line in lines
    ) + '\n')
    env_path.chmod(0o600)
    print(f'Attached pilot bot to inbox {args.inbox}. Credentials saved privately in .env.')
    print('Now run: docker-compose up -d --force-recreate bot')


if __name__ == '__main__':
    main()
