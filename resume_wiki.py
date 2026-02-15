import csv
import json
import urllib.request
import urllib.parse
import time
import os

INPUT = '/sessions/brave-dreamy-ride/mesh_filtered.csv'
CHECKPOINT = '/sessions/brave-dreamy-ride/wiki_checkpoint.json'

with open(INPUT) as f:
    records = list(csv.DictReader(f))

titles = [r['name'] for r in records]

with open(CHECKPOINT) as f:
    checked = json.load(f)

# Also re-check ERRORs
to_check = [t for t in titles if t not in checked or checked[t] == 'ERROR']
print(f"Remaining to check: {len(to_check)}")

BATCH_SIZE = 50
API_URL = "https://en.wikipedia.org/w/api.php"

def check_batch(title_batch):
    params = {
        'action': 'query',
        'titles': '|'.join(title_batch),
        'format': 'json',
        'redirects': '1'
    }
    url = API_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'MeSHWikiBot/1.0 (research project)'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
    results = {}
    redirect_map = {}
    if 'redirects' in data.get('query', {}):
        for redir in data['query']['redirects']:
            redirect_map[redir['from']] = redir['to']
    norm_map = {}
    if 'normalized' in data.get('query', {}):
        for norm in data['query']['normalized']:
            norm_map[norm['from']] = norm['to']
    
    pages = data.get('query', {}).get('pages', {})
    existing_titles = set()
    for pid, page in pages.items():
        if int(pid) > 0:
            existing_titles.add(page['title'])
    
    for title in title_batch:
        current = title
        if current in norm_map:
            current = norm_map[current]
        if current in redirect_map:
            current = redirect_map[current]
        results[title] = 'EXISTS' if current in existing_titles else 'MISSING'
    
    return results

for i in range(0, len(to_check), BATCH_SIZE):
    batch = to_check[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(to_check) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for attempt in range(3):
        try:
            results = check_batch(batch)
            checked.update(results)
            break
        except Exception as e:
            wait = (attempt + 1) * 3
            print(f"  Batch {batch_num}: {e}, waiting {wait}s...")
            time.sleep(wait)
    
    if batch_num % 20 == 0 or batch_num == total_batches:
        print(f"  Batch {batch_num}/{total_batches}")
    
    time.sleep(0.5)  # slower rate

# Save
with open(CHECKPOINT, 'w') as f:
    json.dump(checked, f)

exists = sum(1 for v in checked.values() if v == 'EXISTS')
missing = sum(1 for v in checked.values() if v == 'MISSING')
error = sum(1 for v in checked.values() if v == 'ERROR')
print(f"\nFinal: {len(checked)} checked (EXISTS: {exists}, MISSING: {missing}, ERROR: {error})")
