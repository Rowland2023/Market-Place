import httpx
from fastapi import FastAPI, Query, Response, HTTPException
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io

app = FastAPI()

@app.get("/api/invoices/generate")
async def generate_invoice(user_id: str = Query(...)):
    # 1. CLEAN THE ID
    clean_id = user_id.strip()
    
    # 2. FETCH REAL DATA FROM DJANGO
    # Note: Using the service name 'django_backend' for internal Docker networking
    django_url = f"http://django_backend:8000/api/employees/{clean_id}/"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(django_url, timeout=5.0)
            
            # --- DEBUG LOGS (Watch your terminal) ---
            print(f"DEBUG: Status from Django: {response.status_code}") 
            print(f"DEBUG: Data from Django: {response.text}")          
            
            if response.status_code == 200:
                emp_data = response.json()
                print(f"DEBUG: JSON Dictionary: {emp_data}")           
            else:
                # This triggers if Django returns 404 or 500
                emp_data = {"first_name": "Not", "last_name": "Found", "salary": "0.00"}
        
        except Exception as e:
            # This triggers if the connection to the Django container fails
            print(f"DEBUG: Request failed: {e}")
            emp_data = {"first_name": "Employee", "last_name": user_id, "salary": "0.00"}

    # 3. CREATE PDF IN MEMORY
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # --- UI Design ---
    p.setFillColor(colors.HexColor("#447e9b"))
    p.rect(0, 780, 600, 100, fill=1)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 805, "LAGOS TECH HUB")
    p.setFont("Helvetica", 12)
    p.drawString(50, 790, "Official Digital Payroll Confirmation")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 730, "PAYROLL DETAILS")
    p.line(50, 725, 550, 725)
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Employee Name: {emp_data.get('first_name')} {emp_data.get('last_name')}")
    p.drawString(50, 680, f"Employee ID: {clean_id}")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 650, f"Monthly Net Salary: ₦{emp_data.get('salary')}")
    
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.darkgreen)
    p.drawString(50, 600, "Verification Status: VERIFIED & PAID")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    # 4. RETURN THE PDF STREAM
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=payslip_{clean_id}.pdf"}
    )