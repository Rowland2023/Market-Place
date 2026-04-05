import os
import io
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Query, Response
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# 1. Load the .env file from the root directory
load_dotenv()

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- NEW: ADD THIS CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 2. CONFIGURATION - Values pulled from .env
# Default to localhost if DJANGO_SERVICE_URL isn't in .env
DJANGO_SERVICE_URL = os.getenv("DJANGO_SERVICE_URL", "http://django-backend:8000")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# Safety check to ensure the key is loaded
if not PAYSTACK_SECRET_KEY:
    print("CRITICAL ERROR: PAYSTACK_SECRET_KEY not found in environment.")

# --- 1. HELPER: UPDATE DJANGO STATUS ---
async def update_order_status(order_id: int, status: str):
    """Tells Django that the payment has been confirmed/processed."""
    url = f"{DJANGO_SERVICE_URL}/api/orders/{order_id}/"
    async with httpx.AsyncClient() as client:
        try:
            # We use PATCH to only update the 'status' field
            response = await client.patch(url, json={"status": status}, timeout=5.0)
            if response.status_code not in [200, 204]:
                print(f"Django update failed with status {response.status_code}")
        except Exception as e:
            print(f"Failed to update Django status: {e}")

# --- 2. HELPER: MARKETPLACE PDF GENERATOR ---
async def generate_marketplace_pdf(order_id: int):
    django_url = f"{DJANGO_SERVICE_URL}/api/orders/{order_id}/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(django_url, headers={"Accept": "application/json"}, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Order data not found")
            order_data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Invoicing Service error: {exc}")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Header - Marketplace Green
    p.setFillColor(colors.HexColor("#2e7d32"))
    p.rect(0, 780, 600, 100, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB - MARKETPLACE")
    p.setFont("Helvetica", 12)
    p.drawString(50, 790, f"Official Receipt | Order Ref: #{order_id}")

    # Table
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 730, "ITEMS PURCHASED")
    p.line(50, 725, 550, 725)

    y = 700
    p.setFont("Helvetica", 11)
    items = order_data.get('items', [])
    for item in items:
        p.drawString(50, y, f"{item.get('product_name')} (x{item.get('quantity')})")
        p.drawRightString(550, y, f"N {item.get('price_at_purchase')}")
        y -= 25

    p.line(50, y + 10, 550, y + 10)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y - 20, f"TOTAL PAID: N {order_data.get('total_price')}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue(), f"receipt_{order_id}.pdf"

# --- 3. PAYSTACK WEBHOOK (Server-to-Server) ---
@app.post("/api/paystack-webhook")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    """Automated listener for Paystack events."""
    if not x_paystack_signature:
        raise HTTPException(status_code=401, detail="No signature provided")

    json_body = await request.body()
    
    # Use hmac.compare_digest to prevent timing attacks
    computed_hmac = hmac.new(
        PAYSTACK_SECRET_KEY.encode(), 
        json_body, 
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed_hmac, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    if data.get('event') == 'charge.success':
        # Safely extract order_id from metadata
        metadata = data['data'].get('metadata', {})
        order_id = metadata.get('order_id')
        if order_id:
            await update_order_status(order_id, "Paid")
            print(f"Order {order_id} verified via webhook.")

    return {"status": "success"}

# --- 4. PAYMENT VERIFY (For React Frontend) ---
@app.post("/api/payments/verify")
async def verify_payment(payload: dict):
    """Explicitly verify a transaction reference from the frontend."""
    reference = payload.get("reference")
    order_id = payload.get("order_id")
    
    if not reference or not order_id:
        raise HTTPException(status_code=400, detail="Missing payment reference or order ID")
    
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        res_data = response.json()
        
        # Check if the transaction was successful on Paystack's end
        if res_data.get("status") is True and res_data["data"]["status"] == "success":
            await update_order_status(order_id, "Paid")
            return {"status": "verified", "data": res_data["data"]}
            
    raise HTTPException(status_code=400, detail="Payment verification failed")

# --- 5. PDF GENERATION ROUTE ---
@app.get("/api/invoices/generate")
async def generate_invoice(order_id: int = Query(None)):
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    
    pdf_content, filename = await generate_marketplace_pdf(order_id)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )