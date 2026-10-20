"""Short build-result notice through the existing Matrix CI bot and room."""
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

number, url, result = sys.argv[1:]
if not number.isdigit() or result not in ('success', 'failure'):
    raise ValueError('Invalid build result')
prefix = 'https://traefik-ha.tail6af6e.ts.net:28000/job/jellyfin-homelab-ci/job/homelab/'
if url != prefix + number + '/':
    raise ValueError('Unexpected build report URL')
token = Path('/run/ci-matrix-token').read_text().strip()
room = Path('/run/ci-matrix-room').read_text().strip()
path = '/_matrix/client/v3/rooms/' + urllib.parse.quote(room,safe='') + '/send/m.room.message/jellyfin-ci-' + number + '-' + result
body = {'msgtype':'m.text','body':f'Jellyfin build #{number}: {result}.\n{url}'}
request = urllib.request.Request('http://127.0.0.1:28008'+path, method='PUT',
    data=json.dumps(body).encode(), headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
with urllib.request.urlopen(request, timeout=20) as response:
    data=json.load(response)
print(json.dumps({'matrix_event_id':data['event_id'],'result':result}))
