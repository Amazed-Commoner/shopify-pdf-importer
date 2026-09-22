from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parser import parse_supplier_pdf
from shopify_connector import push_products_to_shopify

app = FastAPI(
    title="Shopify Supplier PDF Importer",
    description="Parse supplier PDF price lists into Shopify-ready products.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseResponse(BaseModel):
    count: int
    method: str
    products: list[dict[str, Any]]
    errors: list[str]


class ImportResponse(BaseModel):
    mode: str
    store: str | None
    requested: int
    created: int
    failed: int
    results: list[dict[str, Any]]
    note: str | None = None


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Shopify Supplier PDF Importer",
        "docs": "/docs",
        "parse": "POST /parse/shopify-supplier",
        "import": "POST /import/shopify",
    }


@app.post("/parse/shopify-supplier", response_model=ParseResponse)
async def parse_supplier(file: UploadFile = File(...)) -> ParseResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    result = parse_supplier_pdf(pdf_bytes)
    return ParseResponse(**result)


@app.post("/import/shopify", response_model=ImportResponse)
async def import_to_shopify(file: UploadFile = File(...)) -> ImportResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    parsed = parse_supplier_pdf(pdf_bytes)
    if parsed["count"] == 0:
        raise HTTPException(
            status_code=422,
            detail={"message": "No products parsed from PDF.", "errors": parsed["errors"]},
        )

    push_result = await push_products_to_shopify(parsed["products"])
    return ImportResponse(**push_result)
