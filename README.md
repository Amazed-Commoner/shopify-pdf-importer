# Shopify Supplier PDF -> Product Importer API

Demo API built for Upwork Shopify clients.

### Quickstart
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Test
1. Go to http://localhost:8000/docs
2. Upload supplier PDF to /parse/shopify-supplier
3. See JSON output
4. Set env SHOPIFY_STORE and SHOPIFY_TOKEN then call /import/shopify

### Env vars
```
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_TOKEN=shpat_xxxxx
```

### What to show client in Loom
- Upload their PDF
- Show parsed JSON in Swagger
- Show mock Shopify creation log
- ROI: 10 hrs -> 2 mins
