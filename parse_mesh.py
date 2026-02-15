import xml.etree.ElementTree as ET
import csv
import re

print("Parsing MeSH XML...")
tree = ET.parse('/sessions/brave-dreamy-ride/desc2026')
root = tree.getroot()

records = []
for desc in root.findall('DescriptorRecord'):
    uid = desc.find('DescriptorUI').text
    name = desc.find('DescriptorName/String').text
    desc_class = desc.get('DescriptorClass', '')
    
    # Get tree numbers (for topic classification)
    tree_nums = []
    tnl = desc.find('TreeNumberList')
    if tnl is not None:
        for tn in tnl.findall('TreeNumber'):
            tree_nums.append(tn.text)
    
    records.append({
        'uid': uid,
        'name': name,
        'class': desc_class,
        'tree_numbers': ';'.join(tree_nums)
    })

print(f"Total descriptors: {len(records)}")

# Save all records
with open('/sessions/brave-dreamy-ride/mesh_all.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['uid', 'name', 'class', 'tree_numbers'])
    w.writeheader()
    w.writerows(records)

# Show some examples
for r in records[:10]:
    print(f"  {r['uid']}: {r['name']} -> {r['tree_numbers']}")

print(f"\nSaved to mesh_all.csv")
