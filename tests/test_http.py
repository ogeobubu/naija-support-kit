"""Local HTTP contract checks; no external service or model needed."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pilot_http', Path(__file__).resolve().parents[1] / 'bot/app.py')
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


class ChatwootStub(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.headers.get('Authorization') != 'Bearer contract-test':
            self.send_error(401)
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"pending","inbox_id":2}')

    def do_POST(self):
        self.server.posts.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"id":100}')


class HttpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.cw = ThreadingHTTPServer(('127.0.0.1', 0), ChatwootStub)
        cls.cw.posts = []
        cls.env = patch.dict(os.environ, {
            'CHATWOOT_ACCOUNT_ID': '1', 'CHATWOOT_INBOX_ID': '2',
            'CHATWOOT_API_TOKEN': 'contract-test', 'BOT_WEBHOOK_SECRET': 'test-secret',
            'CHATWOOT_URL': f'http://127.0.0.1:{cls.cw.server_port}', 'BOT_MODE': 'faq'
        })
        cls.env.start()
        cls.data = patch.object(bot, 'DATA', Path(cls.temp.name))
        cls.data.start()
        bot.Handler.bot = bot.PilotBot()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), bot.Handler)
        for server in (cls.cw, cls.server):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        for server in (cls.cw, cls.server):
            server.shutdown()
            server.server_close()
        cls.data.stop()
        cls.env.stop()
        cls.temp.cleanup()

    def test_secret_required(self):
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(self.url + '/webhook/wrong', data=b'{}'), timeout=5)
        self.assertEqual(err.exception.code, 403)

    def test_malformed_payload(self):
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(self.url + '/webhook/test-secret', data=b'[]'), timeout=5)
        self.assertEqual(err.exception.code, 400)

    def test_roundtrip_and_duplicate(self):
        event = {'id': 401, 'event': 'message_created', 'message_type': 'incoming', 'private': False, 'account': {'id': 1}, 'conversation': {'id': 10, 'inbox_id': 2, 'status': 'pending'}, 'content': 'delivery to Lekki'}
        req = Request(self.url + '/webhook/test-secret', data=json.dumps(event).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=5) as response:
            self.assertEqual(json.load(response)['result'], 'reply')
        with urlopen(req, timeout=5) as response:
            self.assertEqual(json.load(response)['result'], 'duplicate')
        self.assertEqual(len(self.cw.posts), 1)
        path, payload = self.cw.posts[0]
        self.assertEqual(path, '/api/v1/accounts/1/conversations/10/messages')
        self.assertIn('₦3,000', payload['content'])
        self.assertIs(payload['private'], False)


if __name__ == '__main__':
    unittest.main()
