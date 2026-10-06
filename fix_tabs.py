import gspread
from google.oauth2.credentials import Credentials

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(
    "token.json", ["https://www.googleapis.com/auth/spreadsheets",
                   "https://www.googleapis.com/auth/drive"])
sh = gspread.authorize(creds).open_by_key(SHEET)

# delete old plain-named tabs (keep emoji ones)
OLD = ["Контент", "Видео, звук, рилсы, монтаж", "Парсинг, скрапинг, сбор данных",
       "Рассылки", "Создание сайтов", "SEO", "SMM и соцсети", "Боты в мессенджерах",
       "CRM, таблицы и учет", "Основа для своего сервиса", "Нейросетевые помощники",
       "Генерация картинок", "Базы и бэкенд", "Разобрать", "Топ недели", "Каталог", "Старт"]
for t in OLD:
    try:
        sh.del_worksheet(sh.worksheet(t))
        print("deleted", t, flush=True)
    except Exception as e:
        print("skip", t, str(e)[:60], flush=True)

# rename emoji tabs to plain (keep emoji prefix)
RENAME = {"📝 Контент": "Контент", "🎬 Видео, звук, рилсы, монтаж": "Видео, звук, рилсы, монтаж",
          "🕷 Парсинг, скрапинг, сбор данных": "Парсинг, скрапинг, сбор данных",
          "📨 Рассылки": "Рассылки", "🌐 Создание сайтов": "Создание сайтов",
          "🔍 SEO": "SEO", "📣 SMM и соцсети": "SMM и соцсети",
          "🤖 Боты в мессенджерах": "Боты в мессенджерах",
          "🗂 CRM, таблицы и учет": "CRM, таблицы и учет",
          "🚀 Основа для своего сервиса": "Основа для своего сервиса",
          "🧠 Нейросетевые помощники": "Нейросетевые помощники",
          "🎨 Генерация картинок": "Генерация картинок",
          "🗄 Базы и бэкенд": "Базы и бэкенд", "🏆 Топ недели": "Топ недели",
          "🏠 Старт": "Старт"}
for old, new in RENAME.items():
    try:
        w = sh.worksheet(old)
        w.update_title(new)
        print("renamed", old, "->", new, flush=True)
    except Exception as e:
        print("rename skip", old, str(e)[:60], flush=True)

print("final:", [w.title for w in sh.worksheets()])
