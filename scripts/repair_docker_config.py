"""Remove an unavailable Docker Desktop credential store after switching to Colima."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile


def main():
    config_dir = Path(os.environ.get('DOCKER_CONFIG', str(Path.home() / '.docker')))
    path = config_dir / 'config.json'
    if not path.exists():
        print('No Docker config exists; no repair needed.')
        return
    original = path.read_bytes()
    config = json.loads(original)
    if config.get('credsStore') != 'desktop':
        print('Docker is not configured to use the Desktop credential store; left unchanged.')
        return
    if shutil.which('docker-credential-desktop'):
        print('Docker Desktop credential helper is installed; left unchanged.')
        return
    if config.get('currentContext') != 'colima':
        raise SystemExit('Select the Colima Docker context before running this repair.')

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = config_dir / ('config.before-colima-repair.' + timestamp + '.json')
    backup_fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(backup_fd, 'wb') as target:
        target.write(original)
    del config['credsStore']
    fd, temp_path = tempfile.mkstemp(prefix='.config-repair-', dir=str(config_dir))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as target:
            json.dump(config, target, indent=2)
            target.write('\n')
        if path.read_bytes() != original:
            raise SystemExit('Docker config changed during repair; retry after other Docker commands finish.')
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    print('Removed only the reference to the missing Desktop credential store.')
    print('Other Docker settings were preserved. Private backup:', backup)


if __name__ == '__main__':
    main()
