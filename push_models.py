"""Push model catalog (FREE/PAID/GO + Statuses + Meta) as FIRST sheets.
Reads C:/opencode/data/model_catalog.json + keys_status.json (source of truth).
Usage: python push_models.py [--sheet SHEET_ID]
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA = "C:/opencode/data"
SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"

PROV_URL = {
    "openrouter": "https://openrouter.ai/settings/keys", "polza": "https://polza.ai",
    "ikhdev-paid": "https://ikhdev.xyz", "ikhdev-free": "https://ikhdev.xyz",
    "ikhdev-bonus": "https://ikhdev.xyz", "groq": "https://console.groq.com/keys",
    "together": "https://api.together.ai/settings/api-keys",
    "fireworks": "https://fireworks.ai/account/api-keys", "chutes": "https://chutes.ai",
    "siliconflow": "https://cloud.siliconflow.com/account/ak",
    "deepinfra": "https://deepinfra.com/dash/api_keys", "aimlapi": "https://aimlapi.com/app/keys",
    "nano-gpt": "https://nano-gpt.com", "novita": "https://novita.ai/settings/key-management",
    "requesty": "https://requesty.ai", "withmartian": "https://withmartian.com",
    "glama": "https://glama.ai", "routerai": "https://routerai.ru/settings/keys",
    "vsegpt": "https://vsegpt.ru", "ohmygpt": "https://ohmygpt.com/apis/keys",
    "aihubmix": "https://console.aihubmix.com", "gptgod": "https://gptgod.online",
    "proxyapi": "https://console.proxyapi.ru",
    "opencode-go": "https://opencode.ai/docs/go/", "opencode": "https://opencode.ai/docs/zen/",
}
PROV_RU = {"openrouter": "openrouter-catalog", "opencode": "zen",
           "ikhdev-paid": "ikhdev платные", "ikhdev-free": "ikhdev бесплатные",
           "ikhdev-bonus": "ikhdev бонус", "polza": "польза"}
CONF_PROV = {"openrouter", "opencode", "opencode-go", "ikhdev-paid", "ikhdev-free",
             "ikhdev-bonus", "polza"}

HDR = ["№", "Модель", "Провайдер", "API", "Статус", "Контекст", "Оценка",
       "Вход $/1M", "Выход $/1M", "Вход ₽", "Выход ₽", "Статус цены",
       "Скидка", "Флаги", "ID для копирования"]

NON_TEXT = ("whisper", "tts", "flux", "sora", "-image", "image-", ":image",
            "audio", "video", "tts-", "imagen", "dall", "midjourney", "veo",
            "kling", "runway")


def is_text(e):
    return not any(x in (e.get("id") or "").lower() for x in NON_TEXT)


def fmt_price(v):
    if v is None:
        return ""
    if v == 0:
        return 0
    return round(float(v), 4)


def flags(e):
    f = []
    if e.get("tools"):
        f.append("tools")
    if e.get("reasoning"):
        f.append("reason")
    if e.get("batch"):
        f.append("batch")
    if e.get("is_router"):
        f.append("авто-роутер")
    if e.get("section") == "free":
        f.append("free · есть лимиты")
    if e.get("stale"):
        f.append("stale")
    return " ".join(f)


def quality(e):
    s = e.get("strength")
    if e.get("is_router"):
        return "авто-роутер"
    if s is None:
        return ""
    src = e.get("quality_source", "")
    tag = {"artificial_analysis_coding": "AA: кодинг · измерено",
           "artificial_analysis_intelligence": "AA: общий интеллект",
           "market_average": "медиана рынка (оценка)"}.get(src, src)
    return f"{s} ({tag})" if tag else str(s)


def prov_name(p):
    return PROV_RU.get(p, p)


def copy_id(e):
    p = e.get("provider", "")
    if p in CONF_PROV and p != "polza":
        return f"{p}/{e.get('id','')}"
    return e.get("id", "")


def status(e):
    s = []
    if e.get("stale"):
        s.append("показаны последние сохранённые данные")
    ps = e.get("price_status", "")
    if ps == "unverified":
        s.append("цена не подтверждена")
    elif ps and ps != "known":
        s.append(ps)
    if e.get("ref_in_per_m") is not None:
        s.append("есть upstream-ориентир (не тариф)")
    return "; ".join(s)


def row(i, e):
    return [i, f"{e.get('id','')} · {e.get('name','')}", prov_name(e.get("provider", "")),
            PROV_URL.get(e.get("provider", ""), ""), status(e),
            e.get("context_length") if e.get("context_length") is not None else "",
            quality(e), fmt_price(e.get("price_in_per_m")), fmt_price(e.get("price_out_per_m")),
            fmt_price(e.get("price_in_rub")), fmt_price(e.get("price_out_rub")),
            e.get("price_status", ""), e.get("discount_pct") if e.get("discount_pct") else "",
            flags(e), copy_id(e)]


def main():
    import gspread
    from google.oauth2.credentials import Credentials
    from improve_sheet import SCOPES, BASE, bu
    sheet_id = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else SHEET
    cat = json.load(open(os.path.join(DATA, "model_catalog.json"), encoding="utf-8"))
    ks = json.load(open(os.path.join(DATA, "keys_status.json"), encoding="utf-8"))
    secs = cat.get("sections", {})

    # checklist §9
    warns = []
    seen = set()
    for sec, arr in secs.items():
        for e in arr:
            for k in ("price_in_per_m", "price_out_per_m"):
                v = e.get(k)
                if v is not None and v < 0:
                    warns.append(f"neg price {e.get('provider')}/{e.get('id')}")
            key = (e.get("provider"), e.get("id"))
            if key in seen:
                warns.append(f"dupe {key}")
            seen.add(key)
            low = (e.get("id") or "").lower()
            if any(x in low for x in ("whisper", "/tts", "flux", "sora", "tts-", "image", "audio", "video")):
                warns.append(f"non-text? {e.get('provider')}/{e.get('id')}")
    print("checklist warns:", len(warns), flush=True)
    for w in warns[:20]:
        print(" ", w, flush=True)

    creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
    sh = gspread.authorize(creds).open_by_key(sheet_id)

    def ensure(title, rows_needed):
        try:
            ws = sh.worksheet(title)
        except Exception:
            ws = sh.add_worksheet(title, rows=rows_needed + 10, cols=len(HDR))
        return ws

    def paint(ws, header, data, color):
        from improve_sheet import bu as _bu
        ws.clear()
        time.sleep(1)
        ws.append_row(header)
        ws.append_row([""])  # promo row, look applied below
        for i in range(0, len(data), 100):
            ws.append_rows([[("" if v is None else v) for v in r] for r in data[i:i + 100]])
            time.sleep(1)
        n = len(data) + 2
        # promo look (same as Топ недели): single line, left, links, height 32
        _segs = [('Рекламное агентство "Гибкий Маркетинг" ', None),
                 ("https://aaik-marketing.ru", "https://aaik-marketing.ru"),
                 (" | 1.3+ млрд рублей заработали клиентам ★ Реализовали > 500 млн рекламного бюджета "
                  "★ Привели > 3 млн лидов/заявок в воронки онлайн-школ и различных бизнесов "
                  "| Посмотри наш ТГ канал - ", None),
                 ("https://t.me/alastartarget", "https://t.me/alastartarget")]
        _runs, _i = [], 0
        for _t, _l in _segs:
            _f = {"bold": True, "fontSize": 13,
                  "foregroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1}}
            if _l:
                _f["foregroundColor"] = {"red": 0.05, "green": 0.3, "blue": 0.8}
                _f["underline"] = True
                _f["link"] = {"uri": _l}
            _runs.append({"startIndex": _i, "format": _f})
            _i += len(_t)
        _bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 1, "endRowIndex": 2,
                                     "startColumnIndex": 0, "endColumnIndex": 1},
                           "cell": {"userEnteredValue": {"stringValue": "".join(t for t, _ in _segs)},
                                    "userEnteredFormat": {
                                        "backgroundColor": {"red": 1, "green": 0.95, "blue": 0.8},
                                        "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE"},
                                    "textFormatRuns": _runs},
                           "fields": "userEnteredValue,userEnteredFormat,textFormatRuns"}}]})
        _bu(sh, {"requests": [{
            "updateDimensionProperties": {
                "range": {"sheetId": ws.id, "dimension": "ROWS", "startIndex": 1, "endIndex": 2},
                "properties": {"pixelSize": 32}, "fields": "pixelSize"}}]})
        r, g, b = int(color[0:2], 16) / 255, int(color[2:4], 16) / 255, int(color[4:6], 16) / 255
        bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1,
                                     "startColumnIndex": 0, "endColumnIndex": len(header)},
                           "cell": {"userEnteredFormat": {
                               "backgroundColor": {"red": r, "green": g, "blue": b},
                               "textFormat": {"bold": True,
                                              "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                               "horizontalAlignment": "CENTER"}},
                           "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment"}}]})
        ws.freeze(rows=1)
        bu(sh, {"requests": [{"setBasicFilter": {"filter": {"range": {
            "sheetId": ws.id, "startRowIndex": 0, "endRowIndex": n,
            "startColumnIndex": 0, "endColumnIndex": len(header)}}}}]})
        return n

    # FREE / PAID / GO (только текстовые модели)
    freer = [e for e in secs.get("free", []) if is_text(e)]
    paidr = [e for e in secs.get("paid", []) if is_text(e)]
    gor = [e for e in secs.get("go", []) if is_text(e)]
    paint(ensure_ws(sh, "⚡ Модели FREE", len(freer)), HDR,
          [row(i + 1, e) for i, e in enumerate(freer)], "2E7D32")
    paint(ensure_ws(sh, "💰 Модели PAID", len(paidr)), HDR,
          [row(i + 1, e) for i, e in enumerate(paidr)], "1565C0")
    goh = ["№", "Модель", "Провайдер", "API", "Статус", "Контекст", "Оценка",
           "Вход $/1M", "Выход $/1M", "Вход ₽", "Выход ₽", "Статус цены",
           "Скидка", "Лимит $/мес", "Лимит ₽/мес", "Флаги", "ID для копирования"]

    def gorow(i, e):
        base = row(i, e)
        lim_u = e.get("monthly_limit_usd")
        lim_r = e.get("monthly_limit_rub")
        return base[:13] + [lim_u if lim_u is not None else "",
                            lim_r if lim_r is not None else ""] + base[13:]
    paint(ensure_ws(sh, "🚀 Open Code GO", len(gor)), goh,
          [gorow(i + 1, e) for i, e in enumerate(gor)], "6A1B9A")

    # Статусы/Мета не заливаем (решение владельца)

    # order: model sheets first
    want = ["⚡ Модели FREE", "💰 Модели PAID", "🚀 Open Code GO", "📡 Статусы", "🧾 Мета",
            "Старт", "Топ недели", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
            "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов", "SEO",
            "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
            "Основа для своего сервиса", "Нейросетевые помощники", "Генерация картинок",
            "Базы и бэкенд", "Маркетинг", "Разобрать"]
    have = {w.title: w for w in sh.worksheets()}
    ordered = [have[t] for t in want if t in have]
    ordered += [w for w in sh.worksheets() if w not in ordered]
    for i, w in enumerate(ordered):
        try:
            sh.batch_update({"requests": [{"updateSheetProperties": {
                "properties": {"sheetId": w.id, "index": i}, "fields": "index"}}]})
            time.sleep(0.5)
        except Exception as e:
            print("idx skip", w.title, str(e)[:50], flush=True)
    print("DONE MODELS")


def ensure_ws(sh, title, rows_needed):
    try:
        return sh.worksheet(title)
    except Exception:
        return sh.add_worksheet(title, rows=rows_needed + 10, cols=17)


if __name__ == "__main__":
    main()
