import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gspread
from google.oauth2.credentials import Credentials
from improve_sheet import (load_rows, ensure_ws, paint_sheet, promo_text, SCOPES, BASE)

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET)

have = {w.title for w in sh.worksheets()}
if "Каталог" in have:
    print("Каталог already exists, nothing to do")
    sys.exit(0)

rows, _ = load_rows(os.path.join(BASE, "catalog.json"))
widths = {0: 50, 1: 240, 2: 100, 3: 460, 4: 380, 5: 300, 6: 100, 7: 90, 8: 110, 9: 80}
master = sh.add_worksheet("Каталог", rows=len(rows) + 10, cols=10)
paint_sheet(sh, master, RU_HEADER := ["№", "Название", "Звезды", "Где пригодится",
                                      "Быстрый старт", "Ссылка", "Язык", "Лицензия",
                                      "Обновлен", "Активен"],
            promo_text(), rows, widths)
try:
    master.update(values=[[e.get("hub", "") for e in [None]]], range_name="K1")  # no-op placeholder
except Exception:
    pass
print("Каталог rebuilt:", len(rows))

# order
WANT = ["Старт", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
        "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов", "SEO",
        "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
        "Основа для своего сервиса", "Нейросетевые помощники", "Генерация картинок",
        "Базы и бэкенд", "Топ недели"]
have = {w.title: w for w in sh.worksheets()}
seq = [have[t] for t in WANT if t in have]
rest = [w for w in sh.worksheets() if w not in seq]
ordered = seq + rest
for i, w in enumerate(ordered):
    try:
        sh.batch_update({"requests": [{"updateSheetProperties": {
            "properties": {"sheetId": w.id, "index": i}, "fields": "index"}}]})
        time.sleep(0.5)
    except Exception as e:
        print("idx skip", w.title, str(e)[:60], flush=True)
print("final:", [w.title for w in sh.worksheets()])
