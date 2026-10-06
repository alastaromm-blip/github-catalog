import json, sys
tfile = sys.argv[1] if len(sys.argv) > 1 else "trans1.txt"
d = json.load(open("catalog.json", encoding="utf-8"))
need = [e for e in d if not e.get("desc_ru")]
trans = {}
for line in open(tfile, encoding="utf-8"):
    line = line.rstrip("\n")
    if "|" not in line:
        continue
    idx, txt = line.split("|", 1)
    trans[int(idx)] = txt.strip()
applied = 0
for gidx, e in enumerate([x for x in d if not x.get("desc_ru")]):
    pass
# map by position in need-list
need_list = [e for e in d if not e.get("desc_ru")]
for idx, txt in trans.items():
    if 0 <= idx < len(need_list) and txt:
        need_list[idx]["desc_ru"] = txt
        applied += 1
json.dump(d, open("catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
left = sum(1 for e in d if not e.get("desc_ru"))
print(f"applied={applied} left={left}")
