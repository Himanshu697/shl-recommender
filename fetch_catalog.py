import urllib.request, json, os

URL = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"

req = urllib.request.Request(URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})
print("Fetching catalog...")
with urllib.request.urlopen(req) as r:
    raw_bytes = r.read()
    text = raw_bytes.decode("utf-8", errors="replace")
    data = json.loads(text, strict=False)

os.makedirs("data", exist_ok=True)
with open("data/catalog.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done. {len(data)} assessments saved to data/catalog.json")