import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Cloud auth: Google OAuth token from env (GSHEET_TOKEN_JSON), fallback to local token.json
env = os.getenv("GSHEET_TOKEN_JSON", "")
tgt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")
if env and not os.path.exists(tgt):
    tok = json.loads(env)
    json.dump(tok, open(tgt, "w"), indent=1)
    print("token from env")
else:
    print("token local")
