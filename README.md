# Shopify Supplier PDF Importer

FastAPI service that parses supplier PDF price lists into Shopify-ready products (SKU, title, price, inventory) and optionally pushes them to the Shopify Admin API.

## Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/` | Service info |
| POST | `/parse/shopify-supplier` | Upload PDF → returns JSON products |
| POST | `/import/shopify` | Upload PDF → parses + pushes to Shopify (mock if no keys) |
| GET | `/docs` | Interactive Swagger UI |

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs

## Push to Shopify (optional)

Set env vars when a client hires you:

```powershell
$env:SHOPIFY_STORE = "your-store.myshopify.com"
$env:SHOPIFY_TOKEN = "shpat_xxxxxxxx"
```

Without these, `/import/shopify` runs in **mock mode** and prints what it *would* create — perfect for demos.

## Deploy (Render)

1. Push this folder to GitHub
2. Render → New → Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Use `https://<your-app>.onrender.com/docs` in proposals

## How parsing works

1. **pdfplumber** — extracts tables (handles 90% of supplier PDFs)
2. **PyMuPDF** — fallback, regex over raw text lines
3. Scanned/image-only PDFs → no results (OCR not included in MVP)
