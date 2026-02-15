import csv
import json
import urllib.request
import urllib.parse
import time
import os

INPUT = '/sessions/brave-dreamy-ride/mesh_filtered.csv'
OUTPUT = '/sessions/brave-dreamy-ride/mesh_wiki_status.csv'
CHECKPOINT = '/sessions/brave-dreamy-ride/wiki_checkpoint.json'

# Load titles
with open(INPUT) as f:
    records = list(csv.DictReader(f))

titles = [r['name'] for r in records]
print(f"Total titles to check: {len(titles)}")

# Load checkpoint if exists
checked = {}
if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT) as f:
        checked = json.load(f)
    print(f"Loaded checkpoint with {len(checked)} already checked")

# Wikipedia API: check 50 titles at a time
BATCH_SIZE = 50
API_URL = "https://en.wikipedia.org/w/api.php"

def check_batch(title_batch):
    """Check if Wikipedia articles exist for a batch of titles."""
    params = {
        'action': 'query',
        'titles': '|'.join(title_batch),
        'format': 'json',
        'redirects': '1'
    }
    url = API_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'MeSHWikiChecker/1.0'})
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    
    results = {}
    
    # Build redirect map
    redirect_map = {}
    if 'redirects' in data.get('query', {}):
        for redir in data['query']['redirects']:
            redirect_map[redir['from']] = redir['to']
    
    # Normalized map
    norm_map = {}
    if 'normalized' in data.get('query', {}):
        for norm in data['query']['normalized']:
            norm_map[norm['from']] = norm['to']
    
    # Check pages
    pages = data.get('query', {}).get('pages', {})
    existing_titles = set()
    for pid, page in pages.items():
        if int(pid) > 0:  # Positive ID means article exists
            existing_titles.add(page['title'])
    
    # Map back to original titles
    for title in title_batch:
        # Follow normalization and redirects
        current = title
        if current in norm_map:
            current = norm_map[current]
        if current in redirect_map:
            current = redirect_map[current]
        
        if current in existing_titles:
            results[title] = 'EXISTS'
        else:
            results[title] = 'MISSING'
    
    return results

# Process in batches
unchecked = [t for t in titles if t not in checked]
total_batches = (len(unchecked) + BATCH_SIZE - 1) // BATCH_SIZE
print(f"Batches to process: {total_batches}")

for i in range(0, len(unchecked), BATCH_SIZE):
    batch = unchecked[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    
    try:
        results = check_batch(batch)
        checked.update(results)
    except Exception as e:
        print(f"  Error on batch {batch_num}: {e}")
        time.sleep(2)
        try:
            results = check_batch(batch)
            checked.update(results)
        except Exception as e2:
            print(f"  Retry failed: {e2}")
            for t in batch:
                checked[t] = 'ERROR'
    
    # Progress
    if batch_num % 50 == 0 or batch_num == total_batches:
        print(f"  Batch {batch_num}/{total_batches} done ({len(checked)} total checked)")
    
    # Checkpoint every 100 batches
    if batch_num % 100 == 0:
        with open(CHECKPOINT, 'w') as f:
            json.dump(checked, f)
    
    # Rate limit: ~1 request per 100ms
    time.sleep(0.1)

# Save final checkpoint
with open(CHECKPOINT, 'w') as f:
    json.dump(checked, f)

# Build final output
for r in records:
    r['wikipedia_status'] = checked.get(r['name'], 'UNKNOWN')

with open(OUTPUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['uid', 'name', 'topic', 'tree_numbers', 'wikipedia_status'])
    w.writeheader()
    w.writerows(records)

# Summary
exists = sum(1 for r in records if r['wikipedia_status'] == 'EXISTS')
missing = sum(1 for r in records if r['wikipedia_status'] == 'MISSING')
errors = sum(1 for r in records if r['wikipedia_status'] not in ('EXISTS', 'MISSING'))
print(f"\n=== SUMMARY ===")
print(f"Total: {len(records)}")
print(f"EXISTS on Wikipedia: {exists} ({100*exists/len(records):.1f}%)")
print(f"MISSING from Wikipedia: {missing} ({100*missing/len(records):.1f}%)")
print(f"Errors: {errors}")

# Topic breakdown
print(f"\n=== MISSING BY TOPIC ===")
topic_missing = {}
topic_total = {}
for r in records:
    t = r['topic']
    topic_total[t] = topic_total.get(t, 0) + 1
    if r['wikipedia_status'] == 'MISSING':
        topic_missing[t] = topic_missing.get(t, 0) + 1

for t in sorted(topic_total, key=lambda x: topic_missing.get(x, 0), reverse=True):
    m = topic_missing.get(t, 0)
    tot = topic_total[t]
    print(f"  {t}: {m}/{tot} missing ({100*m/tot:.1f}%)")
