import requests
from bs4 import BeautifulSoup

FALLBACK_PRODUCTS = [
    {"product": "Running Shoes",    "popularity_score": 95},
    {"product": "Wireless Earbuds", "popularity_score": 88},
    {"product": "Yoga Mat",         "popularity_score": 76},
    {"product": "Coffee Maker",     "popularity_score": 71},
    {"product": "Backpack",         "popularity_score": 65},
]

def get_product_data():
    try:
        url = "https://www.amazon.in/gp/bestsellers"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []
        for item in soup.select(".zg-item-immersion")[:10]:
            img = item.select_one("img")
            if img and img.get("alt"):
                title = img["alt"]
                products.append({
                    "product":          title,
                    "popularity_score": len(title),  # proxy metric
                })

        if products:
            return products

    except Exception as e:
        print(f"[scraper] Warning: could not scrape Amazon ({e}). Using fallback data.")

    return FALLBACK_PRODUCTS
