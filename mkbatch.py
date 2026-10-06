import json, sys
d = json.load(open("catalog.json", encoding="utf-8"))
t = [e for e in d if not e.get("desc_ru")]
n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
off = int(sys.argv[2]) if len(sys.argv) > 2 else 0
batch = t[off:off + n]
print(f"need_total={len(t)} batch={len(batch)}")
with open("batch.txt", "w", encoding="utf-8") as f:
    for i, e in enumerate(batch):
        desc = (e.get("desc_en") or "").replace("\n", " ")[:300]
        f.write(f"{off+i}|{e['full_name']}|{desc}\n")
