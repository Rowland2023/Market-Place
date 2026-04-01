from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderItem, Employee, Payroll
from .serializers import ProductSerializer
from .tasks import trigger_invoice_generation 

# --- 1. HRM: EMPLOYEE DATA API (SAFE VERSION) ---
def employee_detail_api(request, employee_id):
    try:
        # A. Find the Employee
        emp = Employee.objects.get(employee_id=employee_id)
        
        # B. Pull the latest payroll record for the salary amount
        payroll_entry = Payroll.objects.filter(employee=emp).last()
        salary_amount = str(payroll_entry.amount) if payroll_entry else "0.00"
        
        # C. Defensive data retrieval 
        # getattr checks if the field exists, if not, it uses the default string
        f_name = getattr(emp, 'first_name', 'Employee')
        l_name = getattr(emp, 'last_name', employee_id)
        dept = getattr(emp, 'department', 'N/A')
        pos = getattr(emp, 'position', 'N/A')

        return JsonResponse({
            "first_name": f_name,
            "last_name": l_name,
            "salary": salary_amount,
            "department": dept,
            "position": pos
        })
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Employee not found"}, status=404)
    except Exception as e:
        # This will catch and display any other unexpected errors in JSON format
        return JsonResponse({"error": str(e)}, status=500)

# --- 2. MARKETPLACE: CATALOG LOGIC ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# --- 3. MARKETPLACE: TRANSACTION LOGIC ---
@api_view(['POST'])
def create_order(request):
    try:
        data = request.data
        
        new_order = Order.objects.create(
            user_id=data.get('userId'),
            total_price=data.get('total')
        )

        for item in data.get('items', []):
            product = Product.objects.get(id=item['id'])
            OrderItem.objects.create(
                order=new_order,
                product=product,
                quantity=item.get('quantity', 1)
            )

        invoice_payload = {
            "order_id": new_order.id,
            "total_amount": float(data.get('total')),
            "items": data.get('items'),
            "user_id": data.get('userId')
        }

        trigger_invoice_generation.delay(invoice_payload)

        return Response({
            "status": "Accepted",
            "message": "Order received! Your invoice is being processed in the background.",
            "id": new_order.id
        }, status=status.HTTP_201_CREATED)

    except Product.DoesNotExist:
        return Response({"error": "One or more products not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)