# WikiProject MeSH

This project maps every descriptor in the [Medical Subject Headings](https://www.nlm.nih.gov/mesh/meshhome.html) (MeSH) vocabulary to its corresponding Wikipedia article and Wikidata item. The goal is to identify coverage gaps — MeSH terms that should have a Wikipedia article but currently do not.

## Structure

### Scripts

| Script | Description |
|---|---|
| `parse_mesh.py` | Parses the MeSH XML descriptor file and extracts UIDs, names, classes, and tree numbers |
| `filter_v2.py` | Filters and classifies MeSH terms, excluding systematic chemical names and publication types |
| `check_wikipedia.py` | Batch-checks all filtered terms against the Wikipedia API for article existence |
| `resume_wiki.py` | Resumes Wikipedia checking from a checkpoint file (handles rate limiting) |
| `fetch_wikidata.py` | Fetches Wikidata QIDs for each MeSH descriptor via SPARQL queries on property P486 |

### Wikitext pages (`wikitext/`)

- `00_Main_Index.txt` — The WikiProject main page (`Wikipedia:WikiProject MeSH`)
- `01_*.txt` through `37_*.txt` — 37 subpages organized by broad topic area
- `pages_to_upload.json` — Mapping of Wikipedia page titles to filenames

The subpages are grouped into 7 broad areas:

1. **Anatomy and Physiology** (subpages 1–2)
2. **Organisms** (subpages 3–7)
3. **Diseases and Clinical Medicine** (subpages 8–13)
4. **Chemicals, Drugs, and Biochemistry** (subpages 14–25)
5. **Techniques, Equipment, and Health Care** (subpages 26–30)
6. **Biological and Physical Sciences** (subpages 31–33)
7. **Social Sciences, Humanities, and Other** (subpages 34–37)

## Data sources

- **MeSH descriptors**: [NLM MeSH XML download](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/)
- **Topic classification**: Derived from MeSH tree number hierarchy (2nd-level prefixes)
- **Wikidata matching**: Property [P486](https://www.wikidata.org/wiki/Property:P486) (MeSH descriptor ID)
- **Wikipedia existence**: MediaWiki API (`action=query`)

---

## Licence

This project is released into the public domain under the [CC0 1.0 Universal (CC0 1.0) Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).

You can copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.
