from io import BytesIO

import pymupdf


def build_sample_supplier_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)

    lines = [
        "ACME SUPPLY CO. — SPRING PRICE LIST 2026",
        "",
        "SKU          | Product Name          | Price   | Stock",
        "------------ | --------------------- | ------- | ----",
        "SHIRT-001    | Linen Shirt           | 49.99   | 120",
        "PANT-014     | Cotton Chinos         | 59.50   | 85",
        "HAT-003      | Straw Sun Hat         | 24.00   | 200",
        "SOCK-100     | Wool Crew Socks (6pk) | 18.75   | 340",
        "BAG-022      | Canvas Tote Bag       | 32.00   | 75",
        "JKT-007      | Denim Jacket          | 89.99   | 40",
        "SHOE-019     | Leather Loafers       | 110.00  | 60",
        "BELT-005     | Leather Belt          | 35.00   | 150",
        "",
        "Prices are wholesale USD. Stock as of 2026-09-01.",
        "Contact orders@acmesupply.example",
    ]

    y = 72
    for line in lines:
        page.insert_text((54, y), line, fontsize=11, fontname="cour")
        y += 18

    # Page 2 — more items
    page2 = doc.new_page(width=612, height=792)
    lines2 = [
        "ACME SUPPLY CO. — CONTINUED",
        "",
        "SKU          | Product Name          | Price   | Stock",
        "------------ | --------------------- | ------- | ----",
        "CAP-011      | Baseball Cap          | 22.50   | 180",
        "SCF-004      | Silk Scarf            | 28.00   | 95",
        "GLV-008      | Leather Gloves        | 45.00   | 55",
        "VES-002      | Puffer Vest           | 75.00   | 30",
    ]
    y = 72
    for line in lines2:
        page2.insert_text((54, y), line, fontsize=11, fontname="cour")
        y += 18

    buffer = BytesIO()
    doc.save(buffer)
    doc.close()
    return buffer.getvalue()


if __name__ == "__main__":
    data = build_sample_supplier_pdf()
    out = "sample_supplier.pdf"
    with open(out, "wb") as f:
        f.write(data)
    print(f"Wrote {out} ({len(data)} bytes)")
