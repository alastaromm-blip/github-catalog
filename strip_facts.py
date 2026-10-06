import json
d = json.load(open("catalog.json", encoding="utf-8"))
n = 0
for e in d:
    t = e.get("desc_ru", "")
    if " [" in t and t.rstrip().endswith("]"):
        e["desc_ru"] = t.rsplit(" [", 1)[0]
        n += 1
json.dump(d, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("stripped:", n)
