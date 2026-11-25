"""Check that the publication guard rejects private files without printing secrets."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicFileTests(unittest.TestCase):
    def audit(self, files, staged, local_env=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            shutil.copyfile(ROOT / 'scripts/check_public_files.py', root / 'scripts/check_public_files.py')
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            if local_env:
                (root / '.env').write_text(local_env)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'add', '--', *staged], cwd=root, check=True, capture_output=True)
            return subprocess.run([os.sys.executable, str(root / 'scripts/check_public_files.py')],
                                  cwd=root, text=True, capture_output=True, timeout=10)

    def test_safe_template_is_allowed(self):
        result = self.audit({'.env.example': 'CHATWOOT_API_TOKEN=\n'}, ['.env.example'])
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_runtime_file_is_rejected(self):
        result = self.audit({'data/conversations.json': '{}'}, ['data/conversations.json'])
        self.assertEqual(result.returncode, 1)
        self.assertIn('private or runtime file', result.stdout)

    def test_local_secret_is_detected_without_disclosure(self):
        secret = 'example-' + 's' * 32
        result = self.audit({'accidental.txt': secret}, ['accidental.txt'],
                            local_env='CHATWOOT_API_TOKEN=' + secret)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(secret, result.stdout)

    def test_github_token_pattern_is_rejected(self):
        token = 'ghp_' + 'A' * 30
        result = self.audit({'accidental.txt': token}, ['accidental.txt'])
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(token, result.stdout)


if __name__ == '__main__':
    unittest.main()
