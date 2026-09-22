import os
from typing import Any

import httpx


def _shopify_config() -> tuple[str | None, str | None]:
    store = os.getenv("SHOPIFY_STORE", "").strip()
    token = os.getenv("SHOPIFY_TOKEN", "").strip()
    if store and token:
        if not store.startswith("http"):
            store = f"https://{store}"
        return store.rstrip("/"), token
    return None, None


async def push_products_to_shopify(products: list[dict[str, Any]]) -> dict[str, Any]:
    store, token = _shopify_config()

    if not store or not token:
        created = [
            {
                "status": "mock",
                "message": f"[MOCK] Would create: {p.get('title', '')} "
                f"(SKU {p.get('sku', '')}, ${p.get('price', 0)})",
            }
            for p in products
        ]
        return {
            "mode": "mock",
            "store": None,
            "requested": len(products),
            "created": 0,
            "failed": 0,
            "results": created,
            "note": "Set SHOPIFY_STORE and SHOPIFY_TOKEN env vars to push for real.",
        }

    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }

    created = 0
    failed = 0
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for product in products:
            payload = {
                "product": {
                    "title": product.get("title") or product.get("sku") or "Untitled",
                    "vendor": "PDF Importer",
                    "products_type": "Default",
                    "status": "draft",
                    "variants": [
                        {
                            "price": str(product.get("price") or 0),
                            "sku": product.get("sku") or "",
                            "inventory_quantity": int(product.get("inventory") or 0),
                        }
                    ],
                }
            }
            if product.get("description"):
                payload["product"]["body_html"] = product["description"]

            try:
                resp = await client.post(f"{store}/admin/api/2024-01/products.json", json=payload)
                if resp.status_code in (200, 201):
                    created += 1
                    results.append({"status": "created", "sku": product.get("sku"), "title": product.get("title")})
                else:
                    failed += 1
                    results.append(
                        {
                            "status": "failed",
                            "sku": product.get("sku"),
                            "code": resp.status_code,
                            "body": resp.text[:300],
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                results.append({"status": "error", "sku": product.get("sku"), "error": str(exc)})

    return {
        "mode": "live",
        "store": store,
        "requested": len(products),
        "created": created,
        "failed": failed,
        "results": results,
    }
