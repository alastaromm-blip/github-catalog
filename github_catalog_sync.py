"""Variant B: Python outside the Sheet writes data via Sheets API.
Usage:
  python github_catalog_sync.py seeds --config config.json --out seeds.json
  python github_catalog_sync.py enrich --seeds seeds.json --out catalog.json
  python github_catalog_sync.py push --catalog catalog.json --sheet SHEET_ID
  python github_catalog_sync.py update --sheet SHEET_ID --mode incremental
Env: GITHUB_TOKEN, GOOGLE_CREDS_JSON (service account path or JSON string).
"""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone

import requests
from requests.exceptions import ConnectionError as ConnErr, Timeout as ReqTimeout

from catalog_utils import dedupe_repos, hub_for_topics, parse_repo_url

API = "https://api.github.com"
HEADERS = lambda tok: {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"}

REPO_RE = re.compile(r"github\.com/([\w.\-]+/[\w.\-]+)", re.I)

INSTALL_PATTERNS = [
    (re.compile(r"docker\s+compose\s+up[^\n`]*", re.I), None),
    (re.compile(r"docker\s+run\s+[^\n`]+", re.I), None),
    (re.compile(r"pip\s+install\s+[^\n`&|;]+", re.I), None),
    (re.compile(r"uv\s+add\s+[^\n`&|;]+", re.I), None),
    (re.compile(r"npx\s+[^\n`&|;]+", re.I), None),
    (re.compile(r"npm\s+i(?:nstall)?\s+[^\n`&|;]+", re.I), None),
    (re.compile(r"brew\s+install\s+[^\n`&|;]+", re.I), None),
    (re.compile(r"curl\s+-fsSL\s+\S+\s*\|\s*(?:sudo\s+)?(?:bash|sh)", re.I), None),
]


def parse_install(readme: str, full_name: str) -> str:
    if not readme:
        return f"git clone https://github.com/{full_name}.git"
    text = readme.replace("\r", "\n")
    for pat, _ in INSTALL_PATTERNS:
        m = pat.search(text)
        if m:
            cmd = m.group(0).strip().rstrip("\\").strip()
            if len(cmd) > 220:
                cmd = cmd[:220]
            return cmd
    return f"git clone https://github.com/{full_name}.git"


def stars_human(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        return f"⭐{n}"
    if n >= 1000:
        val = n / 1000
        s = f"{val:.1f}".replace(".", ",").rstrip("0").rstrip(",") if val < 100 else str(int(val))
        return f"⭐{s} тыс."
    return f"⭐{n}"

CATALOG_HEADER = ["hub_ru", "sub", "full_name", "url", "desc_en", "desc_ru", "stars",
                  "forks", "pushed_at", "language", "license", "topics", "active", "updated_at", "source"]


def gh_get(path, token, params=None, retries=3):
    import time as _t
    last = None
    for i in range(retries):
        try:
            r = requests.get(f"{API}{path}", headers=HEADERS(token), params=params, timeout=30)
        except (ConnErr, ReqTimeout) as e:
            last = e
            wait = 10 * (i + 1)
            print(f"net error, wait {wait}s ({path}): {e}", flush=True)
            _t.sleep(wait)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (403, 429):
            wait = int(r.headers.get("Retry-After", 60))
            print(f"rate-limit, wait {wait}s ({path})", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
    raise RuntimeError(f"failed {path}: {last}")


def collect_from_topics(cfg, token, per_topic=100):
    per_hub = cfg.get("max_per_hub", 115)
    all_found = []
    for hub in cfg["hubs"]:
        hub_found = []
        for topic in hub.get("topics", []):
            q = f"topic:{topic} stars:>={cfg.get('min_stars', 50)} pushed:>={cfg.get('pushed_since', '2024-01-01')}"
            data = gh_get("/search/repositories", token, {"q": q, "sort": "stars", "order": "desc", "per_page": min(per_topic, 100)})
            for it in data.get("items", []):
                hub_found.append(it["full_name"])
            time.sleep(2)  # search rate-limit 30/min
        hub_found = dedupe_repos(hub_found)[:per_hub]
        print(f"hub {hub.get('id')}: {len(hub_found)}", flush=True)
        all_found += hub_found
    return dedupe_repos(all_found)[: cfg.get("max_repos", 1000)]


def collect_from_awesome(urls, token):
    found = []
    for u in urls:
        full = parse_repo_url(u)
        try:
            readme = gh_get(f"/repos/{full}/readme", token, {"media": "raw"})
            text = readme if isinstance(readme, str) else json.dumps(readme)
        except Exception as e:
            print(f"awesome skip {full}: {e}")
            continue
        for m in REPO_RE.findall(text):
            found.append(m)
    return dedupe_repos(found)


def enrich(full_names, token, max_days=180, merge_path=None):
    rows = []
    old = {}
    # never shrink: keep previous entries for repos that fail this run
    for p in [merge_path or "catalog.json", "catalog.csv"]:
        try:
            if p.endswith(".json"):
                for e in json.load(open(p, encoding="utf-8")):
                    old[e["full_name"].lower()] = e
                break
        except Exception:
            continue
    now = datetime.now(timezone.utc).isoformat()
    for full in full_names:
        try:
            r = gh_get(f"/repos/{full}", token, retries=5)
            topics = gh_get(f"/repos/{full}/topics", token).get("names", [])
            try:
                rr = requests.get(f"{API}/repos/{full}/readme",
                                  headers={**HEADERS(token),
                                           "Accept": "application/vnd.github.raw"},
                                  timeout=30)
                readme = rr.text if rr.status_code == 200 else ""
            except Exception:
                readme = ""
        except Exception as e:
            print(f"enrich skip {full}: {e}")
            if full.lower() in old:
                rows.append(old[full.lower()])
                print(f"enrich keep old {full}")
            continue
        rows.append({
            "full_name": r["full_name"], "url": r["html_url"],
            "desc_en": r.get("description") or "", "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0), "pushed_at": r.get("pushed_at", ""),
            "language": r.get("language") or "", "license": (r.get("license") or {}).get("spdx_id", ""),
            "topics": topics, "hub": hub_for_topics(topics), "updated_at": now,
            "install": parse_install(readme, r["full_name"]),
            "stars_human": stars_human(r.get("stargazers_count", 0)),
        })
        time.sleep(0.5)
    return rows


def to_sheet_rows(enriched, hub_ru_map):
    out = []
    for e in enriched:
        out.append([hub_ru_map.get(e["hub"], e["hub"]), "", e["full_name"], e["url"],
                    e["desc_en"], "", e["stars"], e["forks"], e["pushed_at"],
                    e["language"], e["license"], ",".join(e["topics"]),
                    "да", e["updated_at"], "api"])
    return out


def push_to_sheet(rows, sheet_id, creds):
    import gspread
    gc = gspread.service_account_from_dict(creds) if isinstance(creds, dict) else gspread.service_account(filename=creds)
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("catalog")
    except Exception:
        ws = sh.add_worksheet("catalog", rows=max(len(rows) + 10, 100), cols=len(CATALOG_HEADER))
    ws.clear()
    ws.append_row(CATALOG_HEADER)
    for i in range(0, len(rows), 100):
        ws.append_rows(rows[i:i + 100])
        print(f"pushed {min(i+100, len(rows))}/{len(rows)}")
    print("done, update triggers: Sheets filter views per hub + top_week sort")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seeds"); s.add_argument("--config", required=True); s.add_argument("--out", required=True)
    e = sub.add_parser("enrich"); e.add_argument("--seeds", required=True); e.add_argument("--out", required=True)
    p = sub.add_parser("push"); p.add_argument("--catalog", required=True); p.add_argument("--sheet", required=True)
    u = sub.add_parser("update"); u.add_argument("--sheet", required=True); u.add_argument("--mode", default="incremental")
    u.add_argument("--config", default="config.json")
    a = ap.parse_args()
    token = os.getenv("GITHUB_TOKEN", "")
    if a.cmd in ("seeds", "enrich", "update") and not token:
        print("need GITHUB_TOKEN"); sys.exit(2)
    if a.cmd == "seeds":
        cfg = json.load(open(a.config, encoding="utf-8"))
        seeds = [parse_repo_url(u) if "github.com" in u else u for u in cfg.get("must_have", [])]
        seeds += collect_from_topics(cfg, token)
        seeds += collect_from_awesome(cfg.get("awesome", []), token)
        seeds = dedupe_repos(seeds)[: cfg.get("max_repos", 1100)]
        json.dump(seeds, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"seeds={len(seeds)} -> {a.out}")
    elif a.cmd == "enrich":
        seeds = json.load(open(a.seeds, encoding="utf-8"))
        rows = enrich(seeds, token)
        json.dump(rows, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"enriched={len(rows)} -> {a.out}")
    elif a.cmd == "push":
        cat = json.load(open(a.catalog, encoding="utf-8"))
        hub_ru = json.load(open("config.json", encoding="utf-8")).get("hub_ru", {})
        rows = to_sheet_rows(cat, hub_ru)
        creds_raw = os.getenv("GOOGLE_CREDS_JSON", "creds.json")
        creds = json.loads(creds_raw) if creds_raw.strip().startswith("{") else creds_raw
        push_to_sheet(rows, a.sheet, creds)
    elif a.cmd == "update":
        print(f"incremental update: re-enrich pushed_at/stars only, sheet={a.sheet} (runs enrich+push)")
        print("tip: schedule daily via Task Scheduler/cron: enrich < full seeds, push")


if __name__ == "__main__":
    main()
