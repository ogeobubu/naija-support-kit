"""Create a synthetic website conversation in the fictional local demo inbox."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:3000'


def request(path, body=None, headers=None, raw=False):
    request_headers = {'Content-Type': 'application/json', 'User-Agent': 'LocalDemoVerification/1.0'}
    request_headers.update(headers or {})
    req = Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=request_headers)
    with urlopen(req, timeout=15) as response:
        data = response.read().decode()
        return data if raw else json.loads(data)


def main():
    demo = json.loads((ROOT / 'data/local-demo.json').read_text())
    env = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines()
               if line and not line.startswith('#') and '=' in line)
    kb = json.loads((ROOT / 'knowledge/business.json').read_text())
    if kb['business'] != 'Lagos Demo Store (fictional)':
        raise SystemExit('Run this check only with the fictional demo knowledge.')
    if (env['CHATWOOT_ACCOUNT_ID'], env['CHATWOOT_INBOX_ID']) != (str(demo['account_id']), str(demo['inbox_id'])):
        raise SystemExit('Connector configuration no longer matches the fictional demo inbox.')
    suffix = '?website_token=' + demo['website_token']
    html = request('/widget' + suffix, raw=True)
    match = re.search(r"window\.authToken\s*=\s*'([^']+)'", html)
    if not match:
        raise RuntimeError('Widget did not return a customer session token.')
    widget_headers = {'X-Auth-Token': match.group(1)}
    bot_headers = {'Authorization': 'Bearer ' + env['CHATWOOT_API_TOKEN']}

    def widget(path, body=None):
        return request('/api/v1/widget/' + path + suffix, body, widget_headers)

    def messages():
        payload = widget('messages')
        if isinstance(payload, list):
            return payload
        for key in ('payload', 'messages'):
            if isinstance(payload.get(key), list):
                return payload[key]
        raise RuntimeError('Unexpected widget messages response.')

    def wait_for_text(fragment):
        for _ in range(30):
            rows = messages()
            if any(fragment in (row.get('content') or '') and row.get('message_type') in (1, 'outgoing') for row in rows):
                return rows
            time.sleep(1)
        raise RuntimeError('Timed out waiting for the expected bot reply: ' + fragment)

    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'account_id': demo['account_id'],
              'inbox_id': demo['inbox_id'], 'checks': []}
    def check(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        if not passed:
            raise RuntimeError(name)

    try:
        created = widget('conversations', {'contact': {'name': 'Local Demo Visitor'}, 'message': {
            'content': 'How much is delivery to Lekki?', 'referer_url': 'http://localhost:3000/local-demo',
            'timestamp': datetime.now(timezone.utc).isoformat()}})
        cid = created.get('id') or created.get('conversation', {}).get('id')
        if not isinstance(cid, int):
            raise RuntimeError('Widget did not return a conversation ID.')
        report['conversation_id'] = cid
        check('customer message reaches Chatwoot', any('delivery to Lekki' in (m.get('content') or '') for m in messages()))
        wait_for_text('Lekki ₦3,000')
        check('approved FAQ reply reaches customer', True)
        widget('messages', {'message': {'content': 'I want to speak to a human'}})
        wait_for_text("I'll pass this to our team")
        state = request(f"/api/v1/accounts/{demo['account_id']}/conversations/{cid}", headers=bot_headers)
        check('handoff opens the conversation for staff', state.get('status') == 'open')
        before = sum(m.get('message_type') in (1, 'outgoing') for m in messages())
        widget('messages', {'message': {'content': 'What are your opening hours?'}})
        time.sleep(5)
        after = sum(m.get('message_type') in (1, 'outgoing') for m in messages())
        check('bot stays silent after handoff during five second observation', after == before)
        report['passed'] = True
    except Exception as error:
        report['passed'] = False
        report['error'] = str(error)
        raise
    finally:
        (ROOT / 'data/live-demo-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print('Report: data/live-demo-report.json', flush=True)


if __name__ == '__main__':
    main()
