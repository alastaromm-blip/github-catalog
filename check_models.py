import json
import urllib.request

with open("C:\\opencode\\opencode.json", encoding="utf-8") as f:
    key = json.load(f)["provider"]["openrouter"]["options"]["apiKey"]

for m in ["google/gemma-3-27b-it:free", "meta-llama/llama-3.3-70b-instruct:free",
          "qwen/qwen3-next-80b-a3b-instruct", "deepseek/deepseek-v3.2:free",
          "cohere/north-mini-code:free"]:
    body = json.dumps({"model": m, "messages": [{"role": "user", "content": "say ok"}],
                       "max_tokens": 5}).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        d = json.loads(r.read().decode())
        print("OK  ", m, "->", d["choices"][0]["message"]["content"][:40].replace("\n", " "))
        break
    except Exception as e:
        print("FAIL", m, str(e)[:120])
