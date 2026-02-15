import csv
import re

# MeSH Tree Number top-level categories
TREE_CATEGORIES = {
    'A': 'Anatomy',
    'B': 'Organisms',
    'C': 'Diseases',
    'D': 'Chemicals and Drugs',
    'E': 'Techniques and Equipment',
    'F': 'Psychiatry and Psychology',
    'G': 'Biological Phenomena and Processes',
    'H': 'Disciplines and Occupations',
    'I': 'Social Sciences',
    'J': 'Technology and Agriculture',
    'K': 'Humanities',
    'L': 'Information Science',
    'M': 'Named Groups',
    'N': 'Health Care',
    'V': 'Publication Characteristics',
    'Z': 'Geographicals',
}

def get_primary_topic(tree_numbers_str):
    if not tree_numbers_str:
        return 'Uncategorized'
    trees = tree_numbers_str.split(';')
    cats = {}
    for t in trees:
        letter = t[0] if t else ''
        if letter in TREE_CATEGORIES:
            cats[letter] = cats.get(letter, 0) + 1
    if not cats:
        return 'Uncategorized'
    best = max(cats, key=cats.get)
    return TREE_CATEGORIES[best]

def is_complex_chemical(name):
    """Detect complex chemical/molecular names that wouldn't make good Wikipedia articles."""
    # Long names with parentheses nesting
    if name.count('(') >= 3:
        return True
    if name.count(',') >= 3:
        return True
    
    # IUPAC-style systematic names
    iupac_indicators = [
        r'\d+,\d+,\d+',          # multiple numbered positions
        r'-(yl|oxy|oyl)-.*-(yl|oxy|oyl)',  # multiple chemical suffixes
        r'^\d.*-\d.*-\d',         # starts with numbered pattern
        r'(alpha|beta|gamma|delta)-\d',
        r'\d+-\(.*\)-\d+',       # numbered-parenthesized-numbered
    ]
    for pat in iupac_indicators:
        if re.search(pat, name, re.IGNORECASE):
            return True
    
    # Very long hyphenated chemical names
    parts = name.split('-')
    if len(parts) >= 4 and any(p.strip().isdigit() or len(p.strip()) <= 2 for p in parts[:3]):
        return True
    
    # Names that are mostly chemical suffixes
    chem_suffixes = ['ase', 'ose', 'ine', 'ide', 'ate', 'ol']
    # This is too broad, skip
    
    return False

def is_meaningful_title(name, tree_numbers_str):
    """Filter out titles that wouldn't make meaningful Wikipedia articles."""
    if len(name) <= 2:
        return False
    
    # Skip very long names (likely complex chemical nomenclature)
    if len(name) > 60:
        return False
    
    # Skip names that are mostly non-alphabetic
    alphanum = re.sub(r'[^a-zA-Z ]', '', name)
    if len(alphanum) < len(name) * 0.5:
        return False
    
    # Skip NOS entries
    if name.endswith(', NOS'):
        return False
    
    # Skip "as Topic" - these are meta-categories
    if 'as Topic' in name:
        return False
    
    # For Chemicals and Drugs (D tree), apply stricter filtering
    is_chem = tree_numbers_str and any(t.startswith('D') for t in tree_numbers_str.split(';'))
    if is_chem:
        if is_complex_chemical(name):
            return False
        # Skip names with numbers embedded in the middle (chemical notation)
        if re.search(r'[a-z]\d+[a-z]', name, re.IGNORECASE):
            # But allow things like "Vitamin B12"
            if not re.search(r'Vitamin|Factor|Type|Class|Group|Phase|Grade', name):
                return False
    
    # Skip publication characteristics
    if tree_numbers_str and all(t.startswith('V') for t in tree_numbers_str.split(';')):
        return False
    
    return True

# Read all records
with open('/sessions/brave-dreamy-ride/mesh_all.csv', 'r') as f:
    reader = csv.DictReader(f)
    records = list(reader)

filtered = []
for r in records:
    name = r['name']
    tree_nums = r['tree_numbers']
    
    if is_meaningful_title(name, tree_nums):
        topic = get_primary_topic(tree_nums)
        filtered.append({
            'uid': r['uid'],
            'name': name,
            'topic': topic,
            'tree_numbers': tree_nums
        })

print(f"Total records: {len(records)}")
print(f"After filtering: {len(filtered)}")

# Topic distribution
topic_counts = {}
for r in filtered:
    t = r['topic']
    topic_counts[t] = topic_counts.get(t, 0) + 1

print("\nTopic distribution:")
for t, c in sorted(topic_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

# Save
with open('/sessions/brave-dreamy-ride/mesh_filtered.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['uid', 'name', 'topic', 'tree_numbers'])
    w.writeheader()
    w.writerows(filtered)

# Show samples per topic
print("\nSamples per topic:")
shown = {}
for r in filtered:
    t = r['topic']
    if t not in shown:
        shown[t] = []
    if len(shown[t]) < 3:
        shown[t].append(r['name'])

for t in sorted(shown):
    print(f"\n  {t}:")
    for s in shown[t]:
        print(f"    - {s}")
