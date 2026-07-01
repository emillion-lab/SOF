import json, urllib.request, base64, os
TOKEN = os.environ.get('GH_TOKEN','')
if not TOKEN: exit(0)
with open('flight-cache.json','rb') as f: content = base64.b64encode(f.read()).decode('ascii')
url = 'https://api.github.com/repos/emillion-lab/BAK/contents/flight-cache.json'
req = urllib.request.Request(url, headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
try:
    with urllib.request.urlopen(req) as r: sha = json.loads(r.read())['sha']
except: sha = None
data = {'message': 'sync: flights from SOF', 'content': content}
if sha: data['sha'] = sha
req2 = urllib.request.Request(url, data=json.dumps(data).encode(), method='PUT', headers={'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github.v3+json'})
try:
    urllib.request.urlopen(req2)
    print('BAK synced!')
except Exception as e: print(f'BAK sync fail: {e}')
