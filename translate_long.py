"""Rewrite desc_ru from desc_long_en via free LLM: 2-4 newbie sentences.
Env: OPENROUTER_KEY. Usage: python translate_long.py [--limit N] [--workers 4]
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

import requests

MODEL = "qwen/qwen3-next-80b-a3b-instruct"
URL = "https://openrouter.ai/api/v1/chat/completions"
BASE = os.path.dirname(os.path.abspath(__file__))


def rewrite(session, name, long_en, short_ru):
    if not long_en or not long_en.strip():
        return ""
    prompt = ("Опиши GitHub-проект для новичка по-русски, 2-4 предложения, простым языком без жаргона: "
              "что это, кому пригодится, чем выделяется. Только текст описания, без заголовков.\n"
              f"Проект: {name}\nОписание: {long_en[:1200]}")
    for attempt in range(3):
        try:
            r = session.post(URL, json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
                             timeout=90)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            print("llm", r.status_code, r.text[:150], flush=True)
            time.sleep(8 * (attempt + 1))
        except Exception as e:
            print("llm err:", str(e)[:100], flush=True)
            time.sleep(8 * (attempt + 1))
    return ""


def main():
    key = os.getenv("OPENROUTER_KEY", "")
    if not key:
        print("need OPENROUTER_KEY"); sys.exit(2)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    p = os.path.join(BASE, "catalog.json")
    data = json.load(open(p, encoding="utf-8"))
    todo = [(i, e) for i, e in enumerate(data)
            if e.get("desc_long_en") and not e.get("desc_ru_long")]
    if limit:
        todo = todo[:limit]
    print(f"to rewrite: {len(todo)}", flush=True)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})

    def job(item):
        i, e = item
        e["desc_ru_long"] = rewrite(s, e["full_name"], e["desc_long_en"], e.get("desc_ru", ""))
        return i

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for _ in ex.map(job, todo):
            done += 1
            if done % 25 == 0:
                json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"rewrote {done}/{len(todo)}", flush=True)
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DONE {done}")


if __name__ == "__main__":
    main()
