import httpx
import io
from fastapi import FastAPI, Query, Response, HTTPException
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

app = FastAPI()

# CHANGE THIS if your docker-compose service is named 'django_app'
DJANGO_SERVICE_URL = "http://django-backend:8000"

# --- HELPER: MARKETPLACE PDF GENERATOR ---
async def generate_marketplace_pdf(order_id: int):
    # Added trailing slash to prevent Django 400/301 redirect issues
    django_url = f"{DJANGO_SERVICE_URL}/api/orders/{order_id}/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                django_url, 
                headers={
                    "Accept": "application/json",
                    "Host": "localhost"  # <--- Add this line},
                },
                timeout=10.0
            ) 
            
            if response.status_code != 200:
                # Log the actual response body to help debugging
                print(f"Django Error Body: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Django returned {response.status_code} for Order ID {order_id}. Ensure order exists."
                )
            order_data = response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Could not connect to Django: {exc}")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Design - Marketplace Green
    p.setFillColor(colors.HexColor("#2e7d32"))
    p.rect(0, 780, 600, 100, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB - MARKETPLACE")
    p.setFont("Helvetica", 12)
    p.drawString(50, 790, f"Official Receipt | Order Ref: #{order_id}")

    # Table Header
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 730, "ITEMS PURCHASED")
    p.line(50, 725, 550, 725)

    y = 700
    p.setFont("Helvetica", 11)
    
    # Loop through items from Django Response
    items = order_data.get('items', [])
    if not items:
        p.drawString(50, y, "No items found for this order.")
    else:
        for item in items:
            p.drawString(50, y, f"{item.get('product_name')} (x{item.get('quantity')})")
            p.drawRightString(550, y, f"N {item.get('price_at_purchase')}")
            y -= 25
            if y < 100: # Simple pagination check
                p.showPage()
                y = 750

    p.line(50, y + 10, 550, y + 10)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y - 20, f"TOTAL PAID: N {order_data.get('total_price')}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue(), f"receipt_{order_id}.pdf"

# --- HELPER: PAYROLL PDF GENERATOR ---
async def generate_payroll_pdf(user_id: str):
    # Ensure this URL matches your Django service name
    django_url = f"http://django-backend:8000/api/employees/{user_id}/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(django_url, timeout=5.0)
            if response.status_code != 200:
                # This will show the error in your terminal logs
                print(f"HRM API Error: {response.status_code} - {response.text}")
                # Fallback only if we absolutely have to, but let's see the error first
                emp_data = {"first_name": "Error", "last_name": "Check Logs", "salary": "0.00", "department": "N/A"}
            else:
                emp_data = response.json()
        except Exception as e:
            print(f"Connection Error: {e}")
            emp_data = {"first_name": "Service", "last_name": "Offline", "salary": "0.00", "department": "N/A"}

    # ... keep the rest of your PDF generation code the same ...
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Design - Corporate Blue
    p.setFillColor(colors.HexColor("#1a237e"))
    p.rect(0, 780, 600, 100, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB - HRM")
    p.setFont("Helvetica", 12)
    p.drawString(50, 790, "MONTHLY PAYSLIP")

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 720, "EMPLOYEE INFORMATION")
    p.line(50, 715, 250, 715)
    
    p.setFont("Helvetica", 12)
    # Match the keys from your Django View: 'first_name', 'last_name', 'salary'
    full_name = f"{emp_data.get('first_name')} {emp_data.get('last_name')}"
    p.drawString(50, 690, f"Full Name: {full_name}")
    p.drawString(50, 670, f"Employee ID: {user_id}")
    p.drawString(50, 650, f"Department: {emp_data.get('department', 'General')}")
    
    p.setFont("Helvetica-Bold", 13)
    p.setFillColor(colors.HexColor("#2e7d32"))
    p.drawString(50, 610, f"NET SALARY: N {emp_data.get('salary')}")
    
    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.grey)
    p.drawCentredString(300, 50, "This is a computer-generated document. No signature required.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue(), f"payslip_{user_id}.pdf"

# --- MAIN ROUTE ---
@app.get("/api/invoices/generate")
async def generate_invoice(order_id: int = Query(None), user_id: str = Query(None)):
    if order_id:
        pdf_content, filename = await generate_marketplace_pdf(order_id)
    elif user_id:
        pdf_content, filename = await generate_payroll_pdf(user_id)
    else:
        raise HTTPException(status_code=400, detail="Please provide either order_id or user_id")

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )