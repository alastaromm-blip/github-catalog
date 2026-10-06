import gspread
from google.oauth2.credentials import Credentials

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(
    "token.json", ["https://www.googleapis.com/auth/spreadsheets",
                   "https://www.googleapis.com/auth/drive"])
sh = gspread.authorize(creds).open_by_key(SHEET)
WANT = ["Старт", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
        "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов", "SEO",
        "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
        "Основа для своего сервиса", "Нейросетевые помощники", "Генерация картинок",
        "Базы и бэкенд", "Топ недели"]
have = {w.title: w for w in sh.worksheets()}
seq = [have[t] for t in WANT if t in have]
rest = [w for w in sh.worksheets() if w not in seq]
ordered = seq + rest
reqs = [{"updateSheetProperties": {"properties": {"sheetId": w.id, "index": i},
                                   "fields": "index"}} for i, w in enumerate(ordered)]
sh.batch_update({"requests": reqs})
print("final:", [w.title for w in sh.worksheets()])
