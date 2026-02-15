import urllib.request
import urllib.parse
import json
import time
import os
import csv

CHECKPOINT = '/sessions/brave-dreamy-ride/wikidata_checkpoint.json'
INPUT = '/sessions/brave-dreamy-ride/mesh_wikipedia_analysis.csv'

# Load existing checkpoint
wd_map = {}
if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT) as f:
        wd_map = json.load(f)
    print(f"Loaded checkpoint: {len(wd_map)} items")

# Get all MeSH UIDs
with open(INPUT) as f:
    records = list(csv.DictReader(f))

all_uids = [r['MeSH_UID'] for r in records]
unchecked = [u for u in all_uids if u not in wd_map]
print(f"Total UIDs: {len(all_uids)}, already checked: {len(wd_map)}, remaining: {len(unchecked)}")

# Use Wikidata SPARQL to batch-query by MeSH ID (P486)
# SPARQL endpoint has limits, so query in chunks of ~300 UIDs
SPARQL_URL = "https://query.wikidata.org/sparql"
BATCH = 300

def sparql_batch(uids):
    values = ' '.join(f'"{u}"' for u in uids)
    query = f"""
    SELECT ?item ?meshId WHERE {{
      VALUES ?meshId {{ {values} }}
      ?item wdt:P486 ?meshId .
    }}
    """
    params = {'query': query, 'format': 'json'}
    url = SPARQL_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'MeSHWikiBot/1.0 (research project)',
        'Accept': 'application/sparql-results+json'
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    
    results = {}
    for binding in data['results']['bindings']:
        mesh_id = binding['meshId']['value']
        qid = binding['item']['value'].split('/')[-1]
        results[mesh_id] = qid
    return results

total_batches = (len(unchecked) + BATCH - 1) // BATCH
print(f"SPARQL batches: {total_batches}")

for i in range(0, len(unchecked), BATCH):
    batch = unchecked[i:i+BATCH]
    batch_num = i // BATCH + 1
    
    for attempt in range(3):
        try:
            results = sparql_batch(batch)
            for uid in batch:
                if uid in results:
                    wd_map[uid] = results[uid]
                else:
                    wd_map[uid] = ''  # No Wikidata item
            break
        except Exception as e:
            wait = (attempt + 1) * 5
            print(f"  Batch {batch_num}: {e}, waiting {wait}s...")
            time.sleep(wait)
    
    if batch_num % 10 == 0 or batch_num == total_batches:
        print(f"  Batch {batch_num}/{total_batches} ({sum(1 for v in wd_map.values() if v)} QIDs found)")
    
    # Save checkpoint every 20 batches
    if batch_num % 20 == 0:
        with open(CHECKPOINT, 'w') as f:
            json.dump(wd_map, f)
    
    time.sleep(1.5)  # Be polite to SPARQL endpoint

# Final save
with open(CHECKPOINT, 'w') as f:
    json.dump(wd_map, f)

found = sum(1 for v in wd_map.values() if v)
print(f"\nDone. {found}/{len(wd_map)} MeSH UIDs have Wikidata items")
