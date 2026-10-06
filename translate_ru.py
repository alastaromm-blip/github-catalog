"""Translate desc_en -> desc_ru ('Где пригодится') via OpenRouter free model.
Needs net. Env: OPENROUTER_KEY. Writes desc_ru into catalog.json in place.
Usage: python translate_ru.py [--catalog catalog.json] [--limit 0] [--workers 4]
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

import requests

MODEL = "qwen/qwen3-coder:free"
URL = "https://openrouter.ai/api/v1/chat/completions"


def translate_one(session, desc):
    if not desc or not desc.strip():
        return ""
    prompt = ("Переведи на русский одним-двумя предложениями, простым языком для новичка, "
              "без жаргона. Только перевод/пересказ, без своих добавлений:\n\n" + desc[:600])
    for attempt in range(3):
        try:
            r = session.post(URL, json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
                             timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            print("translate err:", e, flush=True)
            time.sleep(5 * (attempt + 1))
    return ""


def main():
    catalog = sys.argv[sys.argv.index("--catalog") + 1] if "--catalog" in sys.argv else "catalog.json"
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    key = os.getenv("OPENROUTER_KEY", "")
    if not key:
        print("need OPENROUTER_KEY"); sys.exit(2)
    data = json.load(open(catalog, encoding="utf-8"))
    todo = [(i, e) for i, e in enumerate(data) if not e.get("desc_ru") and e.get("desc_en")]
    if limit:
        todo = todo[:limit]
    print(f"to translate: {len(todo)}", flush=True)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})

    def job(item):
        i, e = item
        e["desc_ru"] = translate_one(s, e["desc_en"])
        return i

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i in ex.map(job, todo):
            done += 1
            if done % 25 == 0:
                json.dump(data, open(catalog, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"translated {done}/{len(todo)}", flush=True)
    json.dump(data, open(catalog, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DONE {done}")


if __name__ == "__main__":
    main()
