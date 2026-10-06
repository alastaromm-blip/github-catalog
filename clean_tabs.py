import gspread
from google.oauth2.credentials import Credentials

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
JUNK = ["Видео и звук для постов", "Боты для мессенджеров", "Сбор данных с сайтов",
        "Сайт без программиста", "Таблицы и учет для себя", "Помощники на нейросети",
        "Свои сервисы вместо чужих", "Продвижение и автопомощники", "Лист1", "catalog"]

creds = Credentials.from_authorized_user_file(
    "token.json",
    ["https://www.googleapis.com/auth/spreadsheets",
     "https://www.googleapis.com/auth/drive"])
sh = gspread.authorize(creds).open_by_key(SHEET)
for t in JUNK:
    try:
        sh.del_worksheet(sh.worksheet(t))
        print("deleted", t, flush=True)
    except Exception as e:
        print("skip", t, e, flush=True)
print("left:", [w.title for w in sh.worksheets()])
