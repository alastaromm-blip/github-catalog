import json
p = "catalog.json"
d = json.load(open(p, encoding="utf-8"))
n = 0
for e in d:
    if e.get("desc_ru_long"):
        e["desc_ru"] = e["desc_ru_long"]
        n += 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"swapped={n} total={len(d)}")
giants = ["openclaw/openclaw", "obra/superpowers", "NousResearch/hermes-agent",
          "n8n-io/n8n", "Significant-Gravitas/AutoGPT", "langchain-ai/langchain"]
have = {e["full_name"] for e in d}
print("missing giants:", [g for g in giants if g not in have])
