from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from parser import extract_supplier_products
from shopify_connector import bulk_import

app = FastAPI(title="Shopify Supplier PDF Importer API", version="1.0.0")

@app.get("/")
def health():
    return {"status": "ok", "message": "Shopify PDF Importer API - Upload PDF to /parse/shopify-supplier"}

@app.post("/parse/shopify-supplier")
async def parse_supplier(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    products = extract_supplier_products(pdf_bytes)
    return {"count": len(products), "products": products, "preview_shopify_payload": products[:2]}

@app.post("/import/shopify")
async def import_to_shopify(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    products = extract_supplier_products(pdf_bytes)
    results = bulk_import(products)
    return {"imported": len(results), "results": results}

# Run with: uvicorn main:app --reload --port 8000
