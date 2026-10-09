"""Improve sheet look & navigation, schema like the reference table.
Tabs: Start, Catalog(master RU), 9 hub tabs, Top week. Promo row 2, filters, colors.
Usage: python improve_sheet.py --sheet SHEET_ID [--catalog catalog.json]
"""
import argparse, json, os, time
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
HUB_STYLE = {
    "Контент": ("8A8FA6", "📝"), "Видео, звук, рилсы, монтаж": ("A66A6A", "🎬"),
    "Парсинг, скрапинг, сбор данных": ("4E7FA6", "🕷"), "Рассылки": ("7A8C4A", "📨"),
    "Создание сайтов": ("3F8C7A", "🌐"), "SEO": ("8C6D3F", "🔍"),
    "SMM и соцсети": ("8E5B96", "📣"), "Боты в мессенджерах": ("3F7A8C", "🤖"),
    "CRM, таблицы и учет": ("6B7A5B", "🗂"), "Основа для своего сервиса": ("556B8C", "🚀"),
    "Нейросетевые помощники": ("6C4E9C", "🧠"), "Маркетинг": ("B08968", "📊"), "Генерация картинок": ("9C5B7A", "🎨"),
    "Базы и бэкенд": ("4E8C6B", "🗄"), "Разобрать": ("777777", "🧺"),
    "Каталог": ("294CA6", "📚"), "Старт": ("294CA6", "🏠"), "Топ недели": ("8C743F", "🏆"),
}


def _base_title(title):
    for name in HUB_STYLE:
        if title == name or title.endswith(" " + name) or title == name:
            return name
    for name in HUB_STYLE:
        if name in title:
            return name
    return title


def _hub_color(title):
    c = HUB_STYLE.get(_base_title(title), ("294CA6", ""))[0]
    return int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255


def TAB(name):
    # plain canonical titles; colors come from tabColor/header, not emoji
    return name


RU_HEADER = ["№", "Название", "Звезды", "Где пригодится", "Быстрый старт",
             "Ссылка", "Язык", "Лицензия", "Обновлен", "Активен"]
NCOLS = len(RU_HEADER)
PROMO_TEXT = ('Рекламное агентство "Гибкий Маркетинг" https://aaik-marketing.ru'
              " | 1.3+ млрд рублей заработали клиентам ★ Реализовали > 500 млн рекламного бюджета "
              "★ Привели > 3 млн лидов/заявок в воронки онлайн-школ и различных бизнесов "
              "| Посмотри наш ТГ канал - https://t.me/alastartarget")


def promo_runs():
    segs = [('Рекламное агентство "Гибкий Маркетинг" ', None),
            ("https://aaik-marketing.ru", "https://aaik-marketing.ru"),
            (" | 1.3+ млрд рублей заработали клиентам ★ Реализовали > 500 млн рекламного бюджета "
             "★ Привели > 3 млн лидов/заявок в воронки онлайн-школ и различных бизнесов "
             "| Посмотри наш ТГ канал - ", None),
            ("https://t.me/alastartarget", "https://t.me/alastartarget")]
    out, i = [], 0
    for text, link in segs:
        fmt = {"bold": True, "fontSize": 13,
               "foregroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1}}
        if link:
            fmt["foregroundColor"] = {"red": 0.05, "green": 0.3, "blue": 0.8}
            fmt["underline"] = True
            fmt["link"] = {"uri": link}
        out.append({"startIndex": i, "format": fmt})
        i += len(text)
    return out


def promo_text():
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    return PROMO_TEXT + f" · Обновлено {today}"


def load_rows(catalog_path):
    cat = json.load(open(catalog_path, encoding="utf-8"))
    hub_ru = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))["hub_ru"]
    out = []
    for i, e in enumerate(cat, 1):
        full = e["full_name"]
        out.append([i, full.replace("/", " / "), e.get("stars_human") or e.get("stars", 0),
                    e.get("desc_ru") or e.get("desc_en", "") or "",
                    e.get("install", "") or "", e.get("url", ""),
                    e.get("language", "") or "", e.get("license", "") or "",
                    (e.get("pushed_at", "") or "")[:10], "да",
                    hub_ru.get(e.get("hub", ""), e.get("hub", "")), int(e.get("stars", 0) or 0)])
    return out, hub_ru  # index 10 = hub, index 11 = stars numeric


def ensure_ws(sh, title, rows=1100, cols=12):
    try:
        return sh.worksheet(title)
    except Exception:
        return sh.add_worksheet(title, rows=rows, cols=cols)


def _retry(fn, what, tries=8):
    import time as _t2
    from gspread.exceptions import APIError
    from requests.exceptions import ConnectionError as ConnErr, Timeout as ReqTimeout
    for i in range(tries):
        try:
            return fn()
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", 0)
            if code in (429, 500, 503) and i < tries - 1:
                wait = 20 * (i + 1)
                print(f"quota wait {wait}s ({what})", flush=True)
                _t2.sleep(wait)
                continue
            raise
        except (ConnErr, ReqTimeout, ConnectionAbortedError, ConnectionResetError) as e:
            if i < tries - 1:
                wait = 15 * (i + 1)
                print(f"net wait {wait}s ({what}): {str(e)[:80]}", flush=True)
                _t2.sleep(wait)
                continue
            raise


def bu(sh, body, tries=6):
    """batch_update with backoff on 429/5xx."""
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


def paint_sheet(sh, ws, header, promo, data_rows, widths, star_col=2, date_col=8):
    """header row 1, promo row 2, data from row 3. All static values."""
    n = len(data_rows)
    ws.clear()
    ws.append_row(header)
    ws.append_row([promo] + [""] * (len(header) - 1))
    for i in range(0, n, 100):
        ws.append_rows([[str(v) for v in r[:len(header)]] for r in data_rows[i:i + 100]])
        print(f"  {ws.title}: {min(i+100, n)}/{n}", flush=True)
    total = n + 2
    _hr, _hg, _hb = _hub_color(ws.title)
    _retry(lambda: ws.format(f"A1:{chr(64+len(header))}1",
              {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
               "backgroundColor": {"red": _hr, "green": _hg, "blue": _hb},
               "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}), "fmt-head")
    _retry(lambda: ws.format(f"A2:{chr(64+len(header))}2",
              {"backgroundColor": {"red": 1, "green": 0.95, "blue": 0.8},
               "textFormat": {"bold": True}}), "fmt-promo")
    try:
        bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 1, "endRowIndex": 2,
                                     "startColumnIndex": 0, "endColumnIndex": 1},
                           "cell": {"textFormatRuns": promo_runs()},
                           "fields": "textFormatRuns"}}]})
    except Exception as _e:
        print("promo runs skip:", str(_e)[:60], flush=True)
    _retry(lambda: ws.freeze(rows=2), "freeze"); time.sleep(2)
    print("zebra: already on, skip")
    bu(sh, {"requests": [{"setBasicFilter": {"filter": {"range": {
        "sheetId": ws.id, "startRowIndex": 0, "endRowIndex": total,
        "startColumnIndex": 0, "endColumnIndex": len(header)}}}}]})
    bu(sh, {"requests": [{
        "updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}} for i, w in widths.items()]})
    scol = chr(65 + star_col)
    _retry(lambda: ws.format(f"{scol}3:{scol}{total}", {"wrapStrategy": "CLIP"}), "fmt-clip")
    bu(sh, {"requests": [{
        "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 2,
                                 "endRowIndex": total,
                                 "startColumnIndex": 3, "endColumnIndex": 5},
                       "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP",
                                                      "verticalAlignment": "TOP"}},
                       "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment"}}]})
    bu(sh, {"requests": [{"updateSheetProperties": {
        "properties": {"sheetId": ws.id,
                       "tabColor": {"red": _hr, "green": _hg, "blue": _hb}},
        "fields": "tabColor"}}]})
    dcol = chr(65 + date_col)
    bu(sh, {"requests": [{
        "addConditionalFormatRule": {"rule": {
            "ranges": [{"sheetId": ws.id, "startRowIndex": 2, "endRowIndex": total,
                        "startColumnIndex": star_col, "endColumnIndex": star_col + 1}],
            "gradientRule": {
                "minpoint": {"color": {"red": 1, "green": 1, "blue": 0.8}, "type": "MIN"},
                "maxpoint": {"color": {"red": 0.2, "green": 0.8, "blue": 0.3}, "type": "MAX"}}},
        "index": 0}}]})
    stale = ["2024", "2023", "2022", "2021", "2020", "201",
             "2025-01", "2025-02", "2025-03"]
    bu(sh, {"requests": [{
        "addConditionalFormatRule": {"rule": {
            "ranges": [{"sheetId": ws.id, "startRowIndex": 2, "endRowIndex": total,
                        "startColumnIndex": date_col, "endColumnIndex": date_col + 1}],
            "booleanRule": {"condition": {"type": "TEXT_STARTS_WITH",
                                          "values": [{"userEnteredValue": p}]},
                            "format": {"backgroundColor": {"red": 1, "green": 0.85, "blue": 0.85}}}},
        "index": 0} for p in stale}]})
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--catalog", default=os.path.join(BASE, "catalog.json"))
    ap.add_argument("--skip-master", action="store_true")
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

    rows, hub_ru = load_rows(a.catalog)
    from datetime import datetime as _dt, timezone as _tz
    today = _dt.now(_tz.utc).strftime("%d.%m.%Y")
    widths = {0: 50, 1: 240, 2: 100, 3: 460, 4: 380, 5: 300, 6: 100, 7: 90, 8: 110, 9: 80}

    if a.skip_master:
        master = sh.worksheet("Каталог")
        print("master skipped (exists)", flush=True)
    else:
        print("master...", flush=True)
        master = ensure_ws(sh, "Каталог")
        paint_sheet(sh, master, RU_HEADER, promo_text(), rows, widths)
    try:
        master.update(values=[["hub"]], range_name="K1:K1")
        _retry(lambda: master.update(values=[[r[10]] for r in rows], range_name=f"K3:K{len(rows)+2}"), "hub-col")
        master.format("K1:K1", {"textFormat": {"bold": True}})
    except Exception as e:
        print("hub helper skip:", e)

    hubs = {}
    for r in rows:
        hubs.setdefault(r[10], []).append(r)
    order = [h for h in [hub_ru.get(k, k) for k in
                         ["content", "video", "parsing", "mailing", "sites", "seo",
                          "smm", "bots", "crm", "saas", "ai", "images", "data", "marketing", "other"]] if h in hubs]
    import time as _t
    for h in order:
        print(f"tab {h}...", flush=True)
        _t.sleep(5)
        ws = ensure_ws(sh, TAB(h)[:32], rows=max(len(hubs[h]) + 10, 50))
        paint_sheet(sh, ws, RU_HEADER, promo_text(), hubs[h], widths)

    fresh = sorted([r for r in rows if r[8] >= "2026-01-01"],
                   key=lambda r: r[11], reverse=True)[:150]
    for _med, _mr in zip(["🥇", "🥈", "🥉"], fresh[:3]):
        _mr[0] = f"{_med} {_mr[0]}"
    print("top...", flush=True)
    ws = ensure_ws(sh, TAB("Топ недели"), rows=170)
    paint_sheet(sh, ws, RU_HEADER, promo_text(), fresh, widths)

    start = ensure_ws(sh, TAB("Старт"), rows=30, cols=3)
    start.clear()
    from datetime import datetime, timezone as _tz
    _now = datetime.now(_tz.utc).strftime("%d.%m.%Y %H:%M UTC")
    _banner = f"Обновлено: {_now} · Репозиториев: {len(rows)} · Вкладок: {len(order)+3}"
    start.update(values=[[_banner, "", ""]], range_name="A1:C1")
    bu(sh, {"requests": [{"mergeCells": {"range": {"sheetId": start.id, "startRowIndex": 0,
                                                   "endRowIndex": 1, "startColumnIndex": 0,
                                                   "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}}]})
    start.format("A1:C1", {"textFormat": {"bold": True, "fontSize": 13},
                           "backgroundColor": {"red": 0.91, "green": 0.95, "blue": 1.0},
                           "horizontalAlignment": "CENTER"})
    toc = [["Раздел", "Репозиториев", "Обновлено"],
           ["Весь каталог (лист Каталог)", len(rows), today]]
    for h in order:
        toc.append([h, len(hubs[h]), today])
    toc.append(["Топ недели (свежие + звезды)", len(fresh), today])
    _retry(lambda: start.update(values=toc, range_name=f"A2:C{len(toc)+1}"), "toc")
    start.format("A2:C2", {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                           "backgroundColor": {"red": 0.16, "green": 0.32, "blue": 0.65}})
    start.freeze(rows=2)
    try:
        _want = [TAB("Старт"), TAB("Каталог")] + [TAB(h)[:32] for h in order] + [TAB("Топ недели")]
        _have = {w.title: w for w in sh.worksheets()}
        _seq = [_have[t] for t in _want if t in _have]
        _rest = [w for w in sh.worksheets() if w not in _seq]
        sh.reorder_worksheets(_seq + _rest)
    except Exception as e:
        print("reorder skip:", e)
    print("DONE")


if __name__ == "__main__":
    main()
