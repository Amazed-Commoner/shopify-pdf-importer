import re
from io import BytesIO
from typing import Any

import pdfplumber
import pymupdf


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("$", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    match = re.search(r"\d+", text)
    if not match:
        return None
    try:
        return int(match.group())
    except ValueError:
        return None


def _looks_like_price(value: Any) -> bool:
    if value is None:
        return False
    text = str(value)
    return bool(re.search(r"\d", text)) and (
        "$" in text or re.search(r"\d+[.,]\d{2}", text) is not None
    )


def _looks_like_sku(value: Any) -> bool:
    if value is None:
        return False
    text = _clean(value)
    if not text or len(text) > 40:
        return False
    return bool(re.search(r"[A-Za-z]", text)) and bool(re.search(r"\d", text))


def _header_index(headers: list[str], *keywords: str) -> int | None:
    for i, header in enumerate(headers):
        low = header.lower()
        if any(k in low for k in keywords):
            return i
    return None


def _map_headers(headers: list[str]) -> dict[str, int | None]:
    return {
        "sku": _header_index(headers, "sku", "item #", "item#", "part #", "part#", "code", "product code"),
        "title": _header_index(headers, "title", "name", "product", "description", "item"),
        "price": _header_index(headers, "price", "cost", "msrp", "retail", "unit price"),
        "inventory": _header_index(headers, "stock", "inventory", "qty", "quantity", "on hand", "available"),
        "description": _header_index(headers, "description", "details", "notes"),
    }


def _row_to_product(mapping: dict[str, int | None], row: list[Any], header_len: int) -> dict[str, Any] | None:
    def cell(key: str) -> Any:
        idx = mapping.get(key)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    title = _clean(cell("title"))
    sku = _clean(cell("sku"))
    price = _to_float(cell("price"))

    if not title and not sku:
        return None
    if price is None and not sku:
        return None

    inventory = _to_int(cell("inventory"))
    description = _clean(cell("description"))

    product: dict[str, Any] = {
        "sku": sku or "",
        "title": title or sku,
        "price": price if price is not None else 0.0,
        "inventory": inventory if inventory is not None else 0,
    }
    if description:
        product["description"] = description
    return product


def _extract_with_pdfplumber(pdf_bytes: bytes) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue

                header_row = table[0] or []
                headers = [_clean(h) for h in header_row]
                mapping = _map_headers(headers)

                if any(v is not None for v in mapping.values()):
                    data_rows = table[1:]
                else:
                    # No recognized header: treat first row as data too
                    mapping = {"sku": None, "title": None, "price": None, "inventory": None, "description": None}
                    data_rows = table
                    # Heuristic: guess columns by content
                    sample = table[0]
                    for col_idx, val in enumerate(sample):
                        if mapping["title"] is None and val and not _looks_like_price(val) and not _looks_like_sku(val):
                            # Prefer a text-heavy column for title — checked across rows below
                            pass
                    # Guess by scanning all rows
                    ncols = max(len(r) for r in table if r)
                    title_c, sku_c, price_c, inv_c = None, None, None, None
                    for c in range(ncols):
                        vals = [r[c] if c < len(r) else None for r in table]
                        price_hits = sum(1 for v in vals if _looks_like_price(v))
                        sku_hits = sum(1 for v in vals if _looks_like_sku(v))
                        text_hits = sum(1 for v in vals if v and len(_clean(v)) > 5 and not _looks_like_price(v))
                        if price_hits >= max(2, len(table) // 3) and price_c is None:
                            price_c = c
                        elif sku_hits >= max(2, len(table) // 3) and sku_c is None:
                            sku_c = c
                        elif text_hits >= max(2, len(table) // 3) and title_c is None:
                            title_c = c
                    mapping = {
                        "sku": sku_c,
                        "title": title_c,
                        "price": price_c,
                        "inventory": inv_c,
                        "description": None,
                    }

                for row in data_rows:
                    if not row:
                        continue
                    product = _row_to_product(mapping, row, len(headers))
                    if not product:
                        continue
                    key = product["sku"] or product["title"]
                    if key in seen:
                        continue
                    seen.add(key)
                    products.append(product)

    return products


def _extract_with_pymupdf(pdf_bytes: bytes) -> list[dict[str, Any]]:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text_parts: list[str] = []
    for page in doc:
        full_text_parts.append(page.get_text("text"))
    doc.close()
    text = "\n".join(full_text_parts)
    return _parse_text_products(text)


def _parse_pipe_row(line: str) -> dict[str, Any] | None:
    if "|" not in line:
        return None
    cells = [c.strip() for c in line.split("|")]
    cells = [c for c in cells if c != ""]
    if len(cells) < 2:
        return None

    sku = ""
    title = ""
    price: float | None = None
    inventory: int | None = None

    for cell in cells:
        if price is None:
            m = re.fullmatch(r"(?:\$|USD\s?)?\s?(\d{1,6}[.,]\d{2})", cell, flags=re.IGNORECASE)
            if m:
                price = _to_float(m.group(1))
                continue
        if not sku and _looks_like_sku(cell) and not re.search(r"\d+[.,]\d{2}", cell):
            if not re.fullmatch(r"\d+", cell):
                sku = cell
                continue
        if inventory is None and re.fullmatch(r"\d{1,6}", cell):
            # Prefer last bare integer as stock when price already seen
            inventory = int(cell)
            continue
        if not title and len(cell) >= 2 and not re.fullmatch(r"\d+", cell):
            if not re.fullmatch(r"(?:\$|USD)?\s?\d+[.,]\d{2}", cell, flags=re.IGNORECASE):
                title = cell

    # If inventory was never set but we stored a bare int early, keep it
    if price is None:
        return None
    if not title and not sku:
        return None

    # Last bare integer after price is stock; re-scan for safer assignment
    bare_ints = [c for c in cells if re.fullmatch(r"\d{1,6}", c)]
    if bare_ints:
        inventory = int(bare_ints[-1])
        # Remove that stock cell from title if it leaked in
        if title and str(inventory) in title:
            title = title.replace(str(inventory), "").strip(" |")

    return {
        "sku": sku,
        "title": title,
        "price": price,
        "inventory": inventory if inventory is not None else 0,
    }


def _parse_text_products(text: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    price_re = re.compile(r"(?:\$|USD\s?)?\s?(\d{1,6}(?:[.,]\d{2}))\b")
    inv_re = re.compile(r"\b(?:qty|stock|inv)[:\s]+(\d{1,6})\b", re.IGNORECASE)
    sku_re = re.compile(r"\b([A-Z0-9][A-Z0-9\-_/]{2,39})\b")

    for line in lines:
        if line.startswith("SKU") or set(line) <= set("|- "):
            continue

        row = _parse_pipe_row(line)
        if row is None:
            price_match = price_re.search(line)
            if not price_match:
                continue
            price = _to_float(price_match.group(1))
            if price is None or price <= 0 or price > 100000:
                continue
            sku_match = sku_re.search(line)
            sku = sku_match.group(1) if sku_match else ""
            title = line.replace(price_match.group(0), " ")
            if sku:
                title = title.replace(sku, " ", 1)
            inv_match = inv_re.search(line)
            inventory = _to_int(inv_match.group(1)) if inv_match else 0
            if inv_match:
                title = title.replace(inv_match.group(0), " ")
            title = re.sub(r"[\s|,;:-]+$", "", title).strip(" |,;:-")
            title = re.sub(r"^(?:SKU|Item|Part)\s*[:#-]?\s*", "", title, flags=re.IGNORECASE).strip()
            row = {
                "sku": sku,
                "title": title,
                "price": price,
                "inventory": inventory or 0,
            }

        sku = row.get("sku") or ""
        title = (row.get("title") or "").strip(" |")
        price = row.get("price")
        inventory = row.get("inventory") or 0

        if not title or len(title) < 2:
            title = sku or f"Item {len(products) + 1}"
        if not sku:
            sku = f"SKU-{len(products) + 1:04d}"

        if sku in seen:
            continue
        seen.add(sku)

        products.append(
            {
                "sku": sku,
                "title": title,
                "price": price if price is not None else 0.0,
                "inventory": inventory,
            }
        )

    return products


def parse_supplier_pdf(pdf_bytes: bytes) -> dict[str, Any]:
    errors: list[str] = []
    products: list[dict[str, Any]] = []
    method = "none"

    try:
        products = _extract_with_pdfplumber(pdf_bytes)
        if products:
            method = "pdfplumber"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pdfplumber failed: {exc}")

    if not products:
        try:
            products = _extract_with_pymupdf(pdf_bytes)
            if products:
                method = "pymupdf"
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pymupdf failed: {exc}")

    if not products and not errors:
        errors.append("No products found. PDF may be scanned/image-only (OCR not enabled) or layout unrecognized.")

    return {
        "count": len(products),
        "method": method,
        "products": products,
        "errors": errors,
    }
