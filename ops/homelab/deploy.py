"""Jenkins deployment plumbing: preserve YAMS, back up stopped Jellyfin, verify health."""
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

ROOT = Path('/srv/homelab/stacks/media/yams')
ARCHIVE = Path('/srv/homelab/archive/jellyfin-ci')
CONFIG = Path('/opt/yams/config/jellyfin')
OVERRIDE = ROOT / 'docker-compose.jellyfin-ci.yaml'


def command(*args, capture=False):
    return subprocess.check_output(args, text=True) if capture else subprocess.run(args, check=True)


def main():
    image, sha = sys.argv[1:]
    if not re.fullmatch('[0-9a-f]{40}', sha) or image != 'local/jellyfin-homelab:' + sha:
        raise ValueError('Expected exact source revision image')
    if command('docker', 'info', '--format', '{{.Name}}', capture=True).strip() != 'docker':
        raise ValueError('Wrong Docker engine')
    revision = command('docker', 'image', 'inspect', image, '--format', '{{index .Config.Labels "org.opencontainers.image.revision"}}', capture=True).strip()
    if revision != sha:
        raise ValueError('Image/source revision mismatch')
    old = json.loads(command('docker', 'inspect', 'jellyfin', capture=True))[0]
    if not old['State']['Running']:
        raise ValueError('Jellyfin is not running; investigate before deployment')
    mounts = old['Mounts']
    if not any(m['Destination'] == '/config' and m['Source'] == str(CONFIG) for m in mounts):
        raise ValueError('Unexpected configuration mount')
    config_size = int(command('du', '-sb', str(CONFIG), capture=True).split()[0])
    if shutil.disk_usage(ARCHIVE).free < config_size + 2 * 1024**3:
        raise ValueError('Insufficient free space for verified rollback backup')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ARCHIVE / (stamp + '-' + sha[:12])
    backup.mkdir(mode=0o700)
    os.umask(0o077)
    previous = OVERRIDE.read_bytes() if OVERRIDE.exists() else None
    (backup / 'previous-image.txt').write_text(old['Image'] + '\n')
    if previous is not None:
        (backup / OVERRIDE.name).write_bytes(previous)
    compose = ['docker', 'compose', '--project-directory', str(ROOT), '-p', 'yams',
        '-f', str(ROOT / 'docker-compose.yaml'), '-f', str(ROOT / 'docker-compose.custom.yaml'), '-f', str(OVERRIDE)]
    OVERRIDE.write_text(json.dumps({'services': {'jellyfin': {'image': image}}}))
    try:
        command(*compose, 'config', '--quiet')
        command('docker', 'stop', '--time', '30', 'jellyfin')
        with tarfile.open(backup / 'config.tar', 'w') as archive:
            archive.add(CONFIG, arcname='config', recursive=True)
        with tarfile.open(backup / 'config.tar', 'r') as archive:
            if not any(member.name.startswith('config/') for member in archive):
                raise ValueError('Empty rollback archive')
        command(*compose, 'up', '-d', '--no-deps', '--no-build', 'jellyfin')
        for attempt in range(36):
            try:
                with urllib.request.urlopen('http://127.0.0.1:28096/health', timeout=5) as response:
                    if response.status == 200:
                        current = json.loads(command('docker', 'inspect', 'jellyfin', capture=True))[0]
                        expected = command('docker', 'image', 'inspect', image, '--format', '{{.Id}}', capture=True).strip()
                        if current['Image'] != expected:
                            raise ValueError('Runtime/image revision mismatch')
                        print(json.dumps({'deployed_sha':sha, 'health':'passed', 'backup':str(backup)}))
                        return
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(5)
        raise RuntimeError('Jellyfin health did not become ready')
    except Exception:
        # Only the pinned 12.0 server is admitted. No automatic DB rollback/migration.
        OVERRIDE.write_text(json.dumps({'services': {'jellyfin': {'image': old['Image']}}}))
        command(*compose, 'up', '-d', '--no-deps', '--no-build', 'jellyfin')
        if previous is not None:
            OVERRIDE.write_bytes(previous)
        else:
            OVERRIDE.unlink()
        raise


if __name__ == '__main__':
    main()
