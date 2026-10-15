#!/usr/bin/env python3
"""WristFit SG Store — price crawler.
Collects SGD prices for tracked models from SG retailers. Writes data/prices.json.
Phase 1 sources (scrape-tolerant, low risk):
  - The Hour Glass AU (AU$, converted SGD) — product pages via search
  - Carousell SG listings (used/grey, ask prices) — via indexed search pages
  - Monards online (AU$) — product pages
Phase 2 (later): Lazada/Shopee via affiliate APIs with keys.
Run: python crawl_prices.py
Output: data/prices.json  { checked_at, models: {slug: [{retailer, price, currency, url, kind}]} }
"""
import json, os, re, sys, time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

def fetch(url, timeout=25):
    try:
        req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
        with urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  ! fetch failed: {url} ({e})", file=sys.stderr)
        return ""

def aud_to_sgd(aud):
    # static-ish fallback rate; crawler records the rate used
    return round(aud * 0.88, 2)

def price_from(html):
    # look for price-like tokens, prefer ones near "price" markup
    m = re.search(r'content="(\d+(?:\.\d{1,2})?)"\s*(?:property="product:price:amount"|itemprop="price")', html)
    if m:
        return float(m.group(1))
    m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d{1,2})?)"?', html)
    if m:
        return float(m.group(1))
    return None

def crawl_hourglass(ref_like):
    """THG search endpoint — returns product page URL + price if found."""
    q = ref_like.split(" ")[0]
    html = fetch(f"https://www.thehourglass.com/en-AU/catalogsearch/result/?q={q}")
    if not html:
        return None
    m = re.search(r'href="(https://www\.thehourglass\.com/en-AU/product/[^"]+)"', html)
    if not m:
        return None
    url = m.group(1)
    page = fetch(url)
    p = price_from(page)
    return {"retailer": "The Hour Glass (AU)", "price_aud": p, "url": url, "kind": "AD"} if p else {"retailer": "The Hour Glass (AU)", "price_aud": None, "url": url, "kind": "AD"}

def crawl_carousell(query):
    """Carousell SG search — indexed snippet prices (fragile; best-effort)."""
    html = fetch(f"https://www.carousell.sg/rtx-5090/q".replace("rtx-5090", "watch-tudor"))
    # NOTE: Carousell blocks bots often; placeholder for API-based phase 2
    return None

def main():
    models_path = os.path.join(BASE, "..", "data", "models.json")
    models = json.load(open(models_path, encoding="utf-8"))
    out = {"checked_at": time.strftime("%Y-%m-%d %H:%M:%S"), "fx_aud_sgd": 0.88, "models": {}}
    for m in models["models"]:
        slug = m["slug"]
        print(f"-> {slug}")
        entries = []
        thg = crawl_hourglass(m.get("ref", m["model"]))
        if thg:
            entries.append(thg)
        out["models"][slug] = entries
        time.sleep(2)  # be polite
    with open(os.path.join(BASE, "..", "data", "prices.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("wrote data/prices.json")

if __name__ == "__main__":
    main()
