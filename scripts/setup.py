"""Create local secrets once. Never overwrites an existing .env."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / '.env'
if target.exists():
    print('.env already exists; left unchanged.')
else:
    content = (root / '.env.example').read_text()
    content = '\n'.join(
        line.replace('GENERATE_WITH_SETUP', secrets.token_hex(32))
        if 'GENERATE_WITH_SETUP' in line else line
        for line in content.splitlines()
    ) + '\n'
    with target.open('x') as handle:
        handle.write(content)
    target.chmod(0o600)
    print('Created .env with unique local secrets.')
(root / 'data').mkdir(exist_ok=True)
