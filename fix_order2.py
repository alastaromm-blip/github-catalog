import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gspread
from google.oauth2.credentials import Credentials
from improve_sheet import SCOPES, BASE

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
sh = gspread.authorize(creds).open_by_key(SHEET)

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
