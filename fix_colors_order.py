"""Fix: 1) move Топ недели after Старт. 2) force hub header colors.
Usage: python fix_colors_order.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gspread
from google.oauth2.credentials import Credentials
from improve_sheet import bu, _hub_color, SCOPES, BASE

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
sh = gspread.authorize(creds).open_by_key(SHEET)
have = {w.title: w for w in sh.worksheets()}

# --- 1. colors: verify + force ---
for t, w in have.items():
    r, g, b = _hub_color(t)
    # header row format
    bu(sh, {"requests": [{
        "repeatCell": {"range": {"sheetId": w.id, "startRowIndex": 0, "endRowIndex": 1,
                                 "startColumnIndex": 0, "endColumnIndex": min(10, w.col_count)},
                       "cell": {"userEnteredFormat": {
                           "backgroundColor": {"red": r, "green": g, "blue": b},
                           "textFormat": {"bold": True,
                                          "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                           "horizontalAlignment": "CENTER"}},
                       "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment"}}]})
    print("colored", t, flush=True)
    time.sleep(1)

# --- 2. order: Старт, Топ недели, Каталог, hubs... ---
WANT = ["Старт", "Топ недели", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
        "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов", "SEO",
        "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
        "Основа для своего сервиса", "Нейросетевые помощники", "Генерация картинок",
        "Базы и бэкенд"]
have = {w.title: w for w in sh.worksheets()}
ordered = [have[t] for t in WANT if t in have]
ordered += [w for w in sh.worksheets() if w not in ordered]
ok = 0
for i, w in enumerate(ordered):
    try:
        sh.batch_update({"requests": [{"updateSheetProperties": {
            "properties": {"sheetId": w.id, "index": i}, "fields": "index"}}]})
        ok += 1
        time.sleep(0.4)
    except Exception as e:
        print("idx skip", w.title, str(e)[:60], flush=True)
print(f"ordered {ok}/{len(ordered)}")
print("final:", [w.title for w in sh.worksheets()])
