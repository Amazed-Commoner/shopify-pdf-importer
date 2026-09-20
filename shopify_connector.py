import requests
import os

SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "your-store.myshopify.com")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN", "shpat_xxx")
API_VERSION = "2024-01"

def create_shopify_product(product: dict):
    """Creates product via Shopify Admin API"""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}
    payload = {
        "product": {
            "title": product["title"],
            "body_html": product.get("body_html", ""),
            "vendor": product.get("vendor", "Supplier Import"),
            "product_type": product.get("product_type", ""),
            "variants": [{"sku": product["sku"], "price": product["price"], "inventory_quantity": product["inventory"]}]
        }
    }
    # For demo, we mock if no token
    if "xxx" in SHOPIFY_TOKEN:
        print(f"[MOCK] Would create: {product['title']} - {product['sku']}")
        return {"id": 123, "mock": True, **product}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()

def bulk_import(products: list):
    results = []
    for p in products:
        results.append(create_shopify_product(p))
    return results
