import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from improve_sheet import load_rows, ensure_ws, paint_sheet, RU_HEADER, promo_text, SCOPES, BASE, TAB
import gspread
from google.oauth2.credentials import Credentials

SHEET = "1XHUL2FDNQC_ZBosZdbAhYEamjf-MT4TkFV_7cXelGrI"
creds = Credentials.from_authorized_user_file(os.path.join(BASE, "token.json"), SCOPES)
if creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    open(os.path.join(BASE, "token.json"), "w").write(creds.to_json())
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET)
rows, _ = load_rows(os.path.join(BASE, "catalog.json"))
widths = {0: 50, 1: 240, 2: 100, 3: 460, 4: 380, 5: 300, 6: 100, 7: 90, 8: 110, 9: 80}
fresh = sorted([r for r in rows if r[8] >= "2026-01-01"], key=lambda r: r[11], reverse=True)[:150]
print("top150:", len(fresh), flush=True)
for _med, _mr in zip(["🥇", "🥈", "🥉"], fresh[:3]):
    _mr[0] = f"{_med} {_mr[0]}"
try:
    sh.del_worksheet(sh.worksheet(TAB("Топ недели")))
except Exception as e:
    print("del skip:", e)
ws = sh.add_worksheet(TAB("Топ недели"), rows=len(fresh) + 10, cols=10)
paint_sheet(sh, ws, RU_HEADER, promo_text(), fresh, widths)
try:
    order = [w.title for w in sh.worksheets()]
    order.remove("Топ недели")
    order.append("Топ недели")
    sh.reorder_worksheets([sh.worksheet(t) for t in order])
except Exception as e:
    print("reorder skip:", e)
print("DONE TOP150")
