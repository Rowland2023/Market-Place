import os
import io
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# 1. Load configuration
load_dotenv()

app = FastAPI()

# --- CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DJANGO_SERVICE_URL = os.getenv("DJANGO_SERVICE_URL", "http://django-backend:8000")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

if not PAYSTACK_SECRET_KEY:
    print("CRITICAL ERROR: PAYSTACK_SECRET_KEY not found in environment.")

# --- 1. HELPER: UPDATE DJANGO STATUS ---
async def update_order_status(order_id: int, status: str):
    """Tells Django that the payment has been confirmed/processed."""
    url = f"{DJANGO_SERVICE_URL}/api/orders/{order_id}/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(url, json={"status": status}, timeout=5.0)
            if response.status_code not in [200, 204]:
                print(f"Django update failed with status {response.status_code}")
        except Exception as e:
            print(f"Failed to update Django status: {e}")

# --- 2. HELPER: MARKETPLACE PDF GENERATOR (WITH DATE) ---
async def generate_marketplace_pdf(order_id: int):
    django_url = f"{DJANGO_SERVICE_URL}/api/orders/{order_id}/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(django_url, headers={"Accept": "application/json"}, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Order data not found")
            order_data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service Unavailable: {exc}")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Header - Marketplace Green
    p.setFillColor(colors.HexColor("#2e7d32"))
    p.rect(0, 780, 600, 100, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB - MARKETPLACE")
    
    # --- Date & Reference Logic ---
    p.setFont("Helvetica", 11)
    order_date = order_data.get('created_at', 'N/A')
    # Clean the ISO string to YYYY-MM-DD
    formatted_date = order_date[:10] if order_date != 'N/A' else 'N/A'
    
    p.drawString(50, 790, f"Official Receipt | Order Ref: #{order_id}")
    p.drawRightString(550, 790, f"Date: {formatted_date}")

    # Items Table
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

# --- 3. HELPER: HRM PAYSLIP GENERATOR ---
async def generate_hrm_payslip_pdf(user_id: str):
    django_url = f"{DJANGO_SERVICE_URL}/api/employees/{user_id}/"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(django_url, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Employee not found")
            emp_data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service Unavailable: {exc}")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Header - HRM Blue
    p.setFillColor(colors.HexColor("#1565c0"))
    p.rect(0, 780, 600, 100, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB - HRM")
    p.setFont("Helvetica", 12)
    p.drawString(50, 790, f"Monthly Payslip | Employee ID: {user_id}")

    # Handle separate first/last name fields from Django
    first = emp_data.get('first_name', '')
    last = emp_data.get('last_name', '')
    full_name = f"{first} {last}".strip() or "N/A"

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 730, f"Employee Name: {full_name}")
    p.line(50, 725, 550, 725)

    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Department: {emp_data.get('department', 'N/A')}")
    p.drawString(50, 680, f"Position: {emp_data.get('position', 'N/A')}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 650, f"Base Salary: N {emp_data.get('salary', '0.00')}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue(), f"payslip_{user_id}.pdf"

# --- 4. WEBHOOKS & VERIFICATION ---
@app.post("/api/paystack-webhook")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    if not x_paystack_signature:
        raise HTTPException(status_code=401, detail="No signature provided")

    json_body = await request.body()
    computed_hmac = hmac.new(PAYSTACK_SECRET_KEY.encode(), json_body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed_hmac, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    if data.get('event') == 'charge.success':
        metadata = data['data'].get('metadata', {})
        order_id = metadata.get('order_id')
        if order_id:
            await update_order_status(order_id, "Paid")

    return {"status": "success"}

@app.post("/api/payments/verify")
async def verify_payment(payload: dict):
    reference = payload.get("reference")
    order_id = payload.get("order_id")
    
    if not reference or not order_id:
        raise HTTPException(status_code=400, detail="Missing payment reference or order ID")
    
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        res_data = response.json()
        
        if res_data.get("status") is True and res_data["data"]["status"] == "success":
            await update_order_status(order_id, "Paid")
            return {"status": "verified", "data": res_data["data"]}
            
    raise HTTPException(status_code=400, detail="Payment verification failed")

# --- 5. UNIFIED PDF GENERATION ROUTE ---
@app.get("/api/invoices/generate")
async def generate_invoice(order_id: int = Query(None), user_id: str = Query(None)):
    if order_id:
        pdf_content, filename = await generate_marketplace_pdf(order_id)
    elif user_id:
        pdf_content, filename = await generate_hrm_payslip_pdf(user_id)
    else:
        raise HTTPException(status_code=400, detail="Provide order_id (Marketplace) or user_id (HRM)")
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )