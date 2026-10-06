"""Fetch READMEs, extract rich intro prose -> desc_long_en.
Usage: python fetch_readme.py (uses GITHUB_TOKEN). Skips entries that already have it.
"""
import json, os, re, sys, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"


def clean_md(text):
    lines = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("![", "[![")) and "](" in s:
            continue  # badges/images
        if re.match(r"^#{1,6}\s", s):
            s = re.sub(r"^#{1,6}\s+", "", s)
            if len(s) < 4:
                continue
        s = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"[*_`~>|#-]", "", s).strip()
        if len(s) < 25:
            continue
        if re.match(r"^(npm|pip|cargo|docker|license|build|test|coverage|version|stars|chat|docs)\b", s, re.I) and len(s) < 60:
            continue
        lines.append(s)
        if sum(len(x) for x in lines) > 900:
            break
    return " ".join(lines)[:900]


def main():
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        print("need GITHUB_TOKEN"); sys.exit(2)
    p = os.path.join(BASE, "catalog.json")
    data = json.load(open(p, encoding="utf-8"))
    todo = [e for e in data if not e.get("desc_long_en")]
    print(f"readme to fetch: {len(todo)}", flush=True)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github.raw"})
    done = 0
    for e in todo:
        try:
            r = s.get(f"{API}/repos/{e['full_name']}/readme", timeout=30)
            e["desc_long_en"] = clean_md(r.text) if r.status_code == 200 else ""
        except Exception as ex:
            print("readme err", e["full_name"], str(ex)[:100], flush=True)
            e["desc_long_en"] = ""
            time.sleep(5)
        done += 1
        if done % 50 == 0:
            json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"readme {done}/{len(todo)}", flush=True)
        time.sleep(0.3)
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DONE have_long={sum(1 for e in data if e.get('desc_long_en'))}")


if __name__ == "__main__":
    main()
