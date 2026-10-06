"""OAuth login as the user (no service account key needed) + push catalog.
Step 1: python oauth_sheet_push.py authurl  -> prints consent URL (open in user's Chrome)
Step 2: user clicks Allow -> code lands on localhost -> saved to token.json
Step 3: python oauth_sheet_push.py push --catalog catalog.json --sheet SHEET_ID
"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
CLIENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oauth_client.json")
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
PORT = 8765

CATALOG_HEADER = ["hub_ru", "sub", "full_name", "url", "desc_en", "desc_ru", "stars",
                  "forks", "pushed_at", "language", "license", "topics", "active", "updated_at", "source"]


def get_flow():
    from google_auth_oauthlib.flow import InstalledAppFlow
    return InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES, redirect_uri=f"http://localhost:{PORT}/")


def cmd_authurl():
    flow = get_flow()
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    print("AUTH_URL:" + url)


def cmd_callback(code):
    flow = get_flow()
    flow.fetch_token(code=code)
    open(TOKEN_FILE, "w").write(flow.credentials.to_json())
    print("token saved")


def cmd_serve_once():
    code_holder = {}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            if "code" in q:
                code_holder["code"] = q["code"][0]
                self.send_response(200); self.end_headers()
                self.wfile.write(b"OK, mojno zakryt vkladku")
            else:
                self.send_response(400); self.end_headers()
                self.wfile.write(b"no code")

        def log_message(self, *a):
            pass

    HTTPServer(("127.0.0.1", PORT), H).handle_request()
    if "code" not in code_holder:
        print("NO_CODE"); sys.exit(1)
    cmd_callback(code_holder["code"])


def cmd_push(catalog_path, sheet_id):
    import gspread
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        open(TOKEN_FILE, "w").write(creds.to_json())
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("catalog")
    except Exception:
        ws = sh.add_worksheet("catalog", rows=1100, cols=len(CATALOG_HEADER))
    cat = json.load(open(catalog_path, encoding="utf-8"))
    hub_ru = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), encoding="utf-8"))["hub_ru"]
    rows = [[hub_ru.get(e.get("hub", ""), e.get("hub", "")), "", e["full_name"], e["url"],
             e.get("desc_en", ""), "", e.get("stars", 0), e.get("forks", 0), e.get("pushed_at", ""),
             e.get("language", ""), e.get("license", ""), ",".join(e.get("topics", [])),
             "yes" if True else "yes", e.get("updated_at", ""), "api"] for e in cat]
    ws.clear()
    ws.append_row(CATALOG_HEADER)
    for i in range(0, len(rows), 100):
        ws.append_rows(rows[i:i + 100])
        print(f"pushed {min(i+100, len(rows))}/{len(rows)}", flush=True)
    print("DONE")


if __name__ == "__main__":
    if sys.argv[1] == "authurl":
        cmd_authurl()
    elif sys.argv[1] == "serve_once":
        cmd_serve_once()
    elif sys.argv[1] == "push":
        import argparse
        ap = argparse.ArgumentParser(); ap.add_argument("--catalog", required=True); ap.add_argument("--sheet", required=True)
        a = ap.parse_args(sys.argv[2:])
        cmd_push(a.catalog, a.sheet)
