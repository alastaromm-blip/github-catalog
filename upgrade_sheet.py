"""Targeted sheet upgrade (no full rewrite):
1. WRAP cols D:E on all data tabs (text fully visible, rows grow).
2. Extend short descs: append language/license/activity facts.
3. Rebuild Top week with 150 rows.
Usage: python upgrade_sheet.py --sheet SHEET_ID [--catalog catalog.json]
"""
import argparse, json, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
DATA_TABS = ["Каталог", "Контент", "Видео, звук, рилсы, монтаж", "Парсинг, скрапинг, сбор данных",
             "Рассылки", "Создание сайтов", "SEO", "SMM и соцсети", "Боты в мессенджерах",
             "CRM, таблицы и учет", "Основа для своего сервиса", "Нейросетевые помощники"]


def bu(sh, body, tries=6):
    import time as _t
    from gspread.exceptions import APIError
    for i in range(tries):
        try:
            return sh.batch_update(body)
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", 0)
            if code in (429, 500, 503) and i < tries - 1:
                wait = 20 * (i + 1)
                print(f"quota wait {wait}s", flush=True)
                _t.sleep(wait)
                continue
            raise


def rich_desc(e):
    base = (e.get("desc_ru") or e.get("desc_en") or "").strip()
    facts = []
    if e.get("language"):
        facts.append(f"язык: {e['language']}")
    if e.get("license"):
        facts.append(f"лицензия: {e['license']}")
    pushed = (e.get("pushed_at") or "")[:10]
    if pushed:
        facts.append(f"активность: {pushed}")
    if e.get("install") and not e["install"].startswith("git clone"):
        facts.append(f"старт: {e['install'][:80]}")
    if facts and len(base) < 400:
        return base + (" — " if base and not base.endswith((".", "!", "?")) else " ") + "[" + "; ".join(facts) + "]" if base else "[" + "; ".join(facts) + "]"
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--catalog", default=os.path.join(BASE, "catalog.json"))
    a = ap.parse_args()

    import gspread
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        open(os.path.join(BASE, "token.json"), "w").write(creds.to_json())
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(a.sheet)
    cat = {e["full_name"]: e for e in json.load(open(a.catalog, encoding="utf-8"))}

    for title in DATA_TABS:
        try:
            ws = sh.worksheet(title)
        except Exception as e:
            print("no tab", title, e, flush=True)
            continue
        sid = ws.id
        nrows = ws.row_count
        # 1. wrap D:E
        bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2,
                                     "startColumnIndex": 3, "endColumnIndex": 5},
                           "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                           "fields": "userEnteredFormat.wrapStrategy"}}]})
        # 2. extend col D by full_name match (col B)
        names = ws.col_values(2)[2:]
        urls = ws.col_values(6)[2:]
        vals = []
        for nm in names:
            full = nm.replace(" / ", "/")
            e = cat.get(full)
            if not e and urls:
                pass
            vals.append([rich_desc(e) if e else ""])
        # find by url fallback
        if urls:
            urlmap = {e.get("url", ""): e for e in cat.values()}
            for i, (nm, u) in enumerate(zip(names, urls)):
                if not vals[i][0] and u in urlmap:
                    vals[i][0] = rich_desc(urlmap[u])
        end = 2 + len(vals)
        bu(sh, {"requests": [{
            "updateCells": {"range": {"sheetId": sid, "startRowIndex": 2,
                                      "endRowIndex": end, "startColumnIndex": 3,
                                      "endColumnIndex": 4},
                            "rows": [{"values": [{"userEnteredValue": {"stringValue": v}}]}
                                     for v in [x[0] for x in vals]],
                            "fields": "userEnteredValue"}}]})
        print(f"{title}: desc extended {len(vals)}", flush=True)
        time.sleep(3)

    print("top150...", flush=True)
    rows = sorted(cat.values(), key=lambda e: int(e.get("stars", 0) or 0), reverse=True)
    fresh = [e for e in rows if (e.get("pushed_at", "") or "") >= "2026-01-01"][:150]
    try:
        sh.del_worksheet(sh.worksheet("Топ недели"))
    except Exception:
        pass
    ws = sh.add_worksheet("Топ недели", rows=len(fresh) + 10, cols=10)
    header = ["№", "Название", "Звезды", "Где пригодится", "Быстрый старт",
              "Ссылка", "Язык", "Лицензия", "Обновлен", "Активен"]
    promo = ("Новинки и разборы каждую неделю — подпишись: Telegram https://t.me/ВАШ_КАНАЛ "
             "| Макс https://max.ru/ВАШ_КАНАЛ (замени ссылки на свои)")
    body = []
    for i, e in enumerate(fresh, 1):
        full = e["full_name"]
        stars = e.get("stars", 0)
        sh_h = f"\u2b50{stars/1000:.1f}".replace(".", ",").rstrip("0").rstrip(",") + " тыс." if stars >= 1000 else f"\u2b50{stars}"
        body.append([i, full.replace("/", " / "), sh_h, rich_desc(e),
                     e.get("install", "") or "", e.get("url", ""),
                     e.get("language", "") or "", e.get("license", "") or "",
                     (e.get("pushed_at", "") or "")[:10], "да"])
    ws.append_row(header)
    ws.append_row([promo] + [""] * 9)
    for i in range(0, len(body), 100):
        ws.append_rows([[str(v) for v in r] for r in body[i:i + 100]])
    ws.format("A1:J1", {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "backgroundColor": {"red": 0.16, "green": 0.32, "blue": 0.65},
                        "horizontalAlignment": "CENTER"})
    ws.format("A2:J2", {"backgroundColor": {"red": 1, "green": 0.95, "blue": 0.8},
                        "textFormat": {"bold": True}})
    ws.freeze(rows=2)
    bu(sh, {"requests": [{"setBasicFilter": {"filter": {"range": {
        "sheetId": ws.id, "startRowIndex": 0, "endRowIndex": len(body) + 2,
        "startColumnIndex": 0, "endColumnIndex": 10}}}}]})
    bu(sh, {"requests": [{
        "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 2,
                                 "startColumnIndex": 3, "endColumnIndex": 5},
                       "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                       "fields": "userEnteredFormat.wrapStrategy"}}]})
    try:
        sh.reorder_worksheets([sh.worksheet(t) for t in
                               ["Старт", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
                                "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов",
                                "SEO", "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
                                "Основа для своего сервиса", "Нейросетевые помощники", "Топ недели"]])
    except Exception as e:
        print("reorder skip:", e)
    print("DONE")


if __name__ == "__main__":
    main()
