import fitz  # PyMuPDF
import pdfplumber
import re

def extract_supplier_products(pdf_bytes: bytes):
    """Extracts SKU, Title, Price, Stock from supplier PDF"""
    products = []
    # Try pdfplumber for table PDFs (90% of supplier lists are tables)
    try:
        import io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:3]:  # demo limit 3 pages
                table = page.extract_table()
                if not table:
                    continue
                # Assume first row is header
                for row in table[1:]:
                    if len(row) < 3: continue
                    # Heuristic mapping - adjust per supplier
                    sku = str(row[0]).strip() if row[0] else ""
                    title = str(row[1]).strip() if len(row)>1 else ""
                    price_raw = str(row[2]).strip() if len(row)>2 else "0"
                    price = float(re.search(r"[\d.]+", price_raw).group()) if re.search(r"[\d.]+", price_raw) else 0.0
                    stock = int(re.search(r"\d+", str(row[3])).group()) if len(row)>3 and re.search(r"\d+", str(row[3])) else 0
                    if sku and title:
                        products.append({"sku": sku, "title": title, "price": price, "inventory": stock, "body_html": f"<p>Imported from supplier PDF - SKU {sku}</p>"})
    except Exception as e:
        print(f"pdfplumber failed: {e}, fallback to PyMuPDF")
        # Fallback text parsing
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join([p.get_text() for p in doc])
        # Simple regex demo
        for m in re.finditer(r"(\w+-\d+)\s+([A-Za-z ]+)\s+\$(\d+\.\d+)", text):
            products.append({"sku": m.group(1), "title": m.group(2).strip(), "price": float(m.group(3)), "inventory": 100})
    return products
