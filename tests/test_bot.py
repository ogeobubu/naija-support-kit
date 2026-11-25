import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bot', Path(__file__).resolve().parents[1] / 'bot/app.py')
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'CHATWOOT_ACCOUNT_ID': '1', 'CHATWOOT_INBOX_ID': '2', 'CHATWOOT_API_TOKEN': 'test', 'BOT_MODE': 'faq'})
        self.env.start()
        self.data = patch.object(bot, 'DATA', Path(self.temp.name))
        self.data.start()
        self.client = bot.PilotBot()
        self.calls = []
        self.status = 'pending'
        def api(cid, suffix='', body=None):
            self.calls.append((cid, suffix, body))
            if suffix == '/toggle_status':
                self.status = body['status']
            return {'id': cid, 'status': self.status, 'inbox_id': 2}
        self.client.api = api
        self.event = {'id': 42, 'event': 'message_created', 'message_type': 'incoming', 'private': False, 'account': {'id': 1}, 'conversation': {'id': 10, 'inbox_id': 2, 'status': 'pending'}, 'content': 'What are your opening hours?'}

    def tearDown(self):
        self.data.stop()
        self.env.stop()
        self.temp.cleanup()

    def messages(self):
        return [call for call in self.calls if call[1] == '/messages']

    def test_approved_answer(self):
        self.assertEqual(self.client.process(self.event), 'reply')
        self.assertIn('9am', self.messages()[0][2]['content'])

    def test_dedup_survives_new_instance(self):
        self.client.process(self.event)
        other = bot.PilotBot()
        other.api = self.client.api
        self.assertEqual(other.process(self.event), 'duplicate')
        self.assertEqual(len(self.messages()), 1)

    def test_wrong_account_or_inbox(self):
        for field in ('account', 'inbox'):
            event = copy.deepcopy(self.event)
            if field == 'account':
                event['account']['id'] = 99
            else:
                event['conversation']['inbox_id'] = 99
            self.assertEqual(self.client.process(event), 'ignored')
        self.assertEqual(self.calls, [])

    def test_outgoing_private_and_other_events(self):
        for replacement in ({'message_type': 'outgoing'}, {'private': True}, {'event': 'conversation_updated'}):
            self.assertEqual(self.client.process(dict(self.event, **replacement)), 'ignored')
        self.assertEqual(self.calls, [])

    def test_payment_handoff_and_stops(self):
        self.event['content'] = 'I have paid, can you confirm payment?'
        self.assertEqual(self.client.process(self.event), 'handoff')
        self.assertEqual(self.status, 'open')
        self.event['id'] += 1
        self.assertEqual(self.client.process(self.event), 'ignored')
        self.assertEqual(len(self.messages()), 1)

    def test_takeover_during_generation(self):
        def generate(*args):
            self.status = 'open'
            return {'action': 'reply', 'content': 'should not send'}
        with patch.object(bot, 'answer', side_effect=generate):
            self.assertEqual(self.client.process(self.event), 'ignored')
        self.assertEqual(self.messages(), [])

    def test_model_failure_hands_off(self):
        with patch.object(bot, 'answer', side_effect=TimeoutError):
            self.assertEqual(self.client.process(self.event), 'handoff')
        self.assertEqual(self.status, 'open')

    def test_uncertain_send_not_retried(self):
        original = self.client.api
        def failing(cid, suffix='', body=None):
            if suffix == '/messages':
                raise TimeoutError()
            return original(cid, suffix, body)
        self.client.api = failing
        self.assertEqual(self.client.process(self.event), 'review_required')
        self.assertEqual(self.client.process(self.event), 'duplicate')
        self.assertEqual(self.status, 'open')

    def test_unknown_and_attachments_handoff(self):
        self.assertEqual(bot.answer('Can you book a flight?')['action'], 'handoff')
        self.event['attachments'] = [{'file_type': 'audio'}]
        self.assertEqual(self.client.process(self.event), 'handoff')

    def test_model_cannot_invent_final_answer(self):
        with patch.object(bot, 'request_json', return_value={'message': {'content': '{"id":"invented"}'}}):
            self.assertEqual(bot.answer('anything', 'ollama')['action'], 'handoff')
        with patch.object(bot, 'request_json', return_value={'message': {'content': '{"id":"hours","answer":"invented"}'}}):
            self.assertNotIn('invented', bot.answer('hours?', 'ollama')['content'])


if __name__ == '__main__':
    unittest.main()
