"""Fixup: recompute hubs offline + fetch missing install cmds.
Usage: python fixup_catalog.py [--catalog catalog.json]
"""
import json, os, sys, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from catalog_utils import hub_for_topics
from github_catalog_sync import parse_install, HEADERS, API


def main():
    catalog = sys.argv[sys.argv.index("--catalog") + 1] if "--catalog" in sys.argv else os.path.join(BASE, "catalog.json")
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        print("need GITHUB_TOKEN"); sys.exit(2)
    data = json.load(open(catalog, encoding="utf-8"))
    for e in data:
        e["hub"] = hub_for_topics(e.get("topics", []))
    print("hubs recomputed", flush=True)
    need = [e for e in data if not e.get("install") or e["install"].startswith("git clone")]
    print(f"install to fetch: {len(need)}", flush=True)
    done = 0
    for e in need:
        try:
            rr = requests.get(f"{API}/repos/{e['full_name']}/readme",
                              headers={**HEADERS(token), "Accept": "application/vnd.github.raw"},
                              timeout=30)
            readme = rr.text if rr.status_code == 200 else ""
        except Exception as ex:
            print("readme err", e["full_name"], ex, flush=True)
            readme = ""
        e["install"] = parse_install(readme, e["full_name"])
        done += 1
        if done % 50 == 0:
            json.dump(data, open(catalog, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"install {done}/{len(need)}", flush=True)
        time.sleep(0.3)
    json.dump(data, open(catalog, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(e.get("hub") for e in data))
    print("real install:", sum(1 for e in data if not e["install"].startswith("git clone")))
    print("DONE")


if __name__ == "__main__":
    main()
