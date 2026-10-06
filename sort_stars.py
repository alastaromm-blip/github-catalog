import json
d = json.load(open("catalog.json", encoding="utf-8"))
d.sort(key=lambda e: int(e.get("stars", 0) or 0), reverse=True)
json.dump(d, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("sorted, top:", d[0]["full_name"], d[0]["stars"])
print("bottom:", d[-1]["full_name"], d[-1]["stars"])
