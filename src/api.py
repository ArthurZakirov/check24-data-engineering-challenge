import json, requests
# in console type: window.router && window.router["frontend.store-api.proxy"]

BASE = "https://www.biermarket.de"
PROXY = f"{BASE}/_proxy/store-api"
CAT   = "7a9c3e9d1e334ad6942e59610459aeed"

s = requests.Session()
hdr = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": f"{BASE}/bier/deutsches-bier/bayern/",
}

s.get(f"{BASE}/bier/deutsches-bier/bayern/", headers=hdr, timeout=20)

r = s.post(f"{PROXY}?path=%2Fstore-api%2Fcontext", headers=hdr, data="{}", timeout=20)
r.raise_for_status()
token = r.json()["token"]
hdr["sw-context-token"] = token

r = s.post(f"{PROXY}?path=%2Fstore-api%2Fproduct-listing%2F{CAT}",
           headers=hdr, data=json.dumps({"page":1,"limit":1}), timeout=20)
print(r.status_code, r.headers.get("content-type"))
print(r.text[:500])
