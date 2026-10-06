"""Enrich only seeds missing from catalog, append. Usage: python enrich_delta.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from github_catalog_sync import enrich

cat = json.load(open("catalog.json", encoding="utf-8"))
have = {e["full_name"].lower() for e in cat}
seeds = json.load(open("seeds.json", encoding="utf-8"))
new = [s for s in seeds if s.lower() not in have]
print(f"have={len(have)} new={len(new)}", flush=True)
if not new:
    print("nothing to do")
    sys.exit(0)
token = os.getenv("GITHUB_TOKEN", "")
rows = enrich(new, token)
cat.extend(rows)
json.dump(cat, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"appended={len(rows)} total={len(cat)}")
