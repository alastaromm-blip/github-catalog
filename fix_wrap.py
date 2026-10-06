import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gspread
from google.oauth2.credentials import Credentials
from improve_sheet import bu, SCOPES, BASE

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
TABS = ["Старт", "Каталог", "Контент", "Видео, звук, рилсы, монтаж",
        "Парсинг, скрапинг, сбор данных", "Рассылки", "Создание сайтов", "SEO",
        "SMM и соцсети", "Боты в мессенджерах", "CRM, таблицы и учет",
        "Основа для своего сервиса", "Нейросетевые помощники", "Генерация картинок",
        "Базы и бэкенд", "Топ недели"]

creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
sh = gspread.authorize(creds).open_by_key(SHEET)

for t in TABS:
    try:
        ws = sh.worksheet(t)
    except Exception as e:
        print("no tab", t, flush=True)
        continue
    # wrap D:E on all data rows (skip header+promo); skip if tab has <5 cols
    if ws.col_count >= 5:
        bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 2,
                                     "endRowIndex": ws.row_count,
                                     "startColumnIndex": 3, "endColumnIndex": 5},
                           "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                           "fields": "userEnteredFormat.wrapStrategy"}}]})
        # vertical top so long text reads well
        bu(sh, {"requests": [{
            "repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 2,
                                     "endRowIndex": ws.row_count,
                                     "startColumnIndex": 0, "endColumnIndex": 10},
                           "cell": {"userEnteredFormat": {"verticalAlignment": "TOP"}},
                           "fields": "userEnteredFormat.verticalAlignment"}}]})
        print("wrapped", t, flush=True)
    else:
        print("skip small tab", t, flush=True)

# Start tab: widen columns
try:
    st = sh.worksheet("Старт")
    bu(sh, {"requests": [{
        "updateDimensionProperties": {
            "range": {"sheetId": st.id, "dimension": "COLUMNS",
                      "startIndex": 0, "endIndex": 3},
            "properties": {"pixelSize": 260}, "fields": "pixelSize"}}]})
    print("start widened", flush=True)
except Exception as e:
    print("start skip", e, flush=True)
print("DONE WRAP")
