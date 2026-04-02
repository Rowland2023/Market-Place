from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes # Add authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product, Order, OrderItem, Employee, Payroll
from .serializers import ProductSerializer
from .tasks import trigger_invoice_generation 

# --- 1. HRM: EMPLOYEE DATA API ---
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([AllowAny]) 
def employee_detail_api(request, employee_id):
    try:
        # 1. Try to find the employee by the exact string provided (e.g., "001")
        emp = Employee.objects.filter(employee_id=employee_id).first()
        
        # 2. If not found, try stripping leading zeros (e.g., "001" -> "1")
        if not emp and employee_id.isdigit():
            emp = Employee.objects.filter(employee_id=employee_id.lstrip('0')).first()
            
        if not emp:
            return Response({"error": f"Employee {employee_id} not found"}, status=404)
        
        # 3. Get Salary: Priority to Payroll table, Fallback to Employee model salary
        payroll_entry = Payroll.objects.filter(employee=emp).last()
        salary_amount = str(payroll_entry.amount) if payroll_entry else str(emp.salary)
        
        return Response({
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "salary": salary_amount,
            "department": emp.department,
            "position": emp.position
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)
# --- 2. MARKETPLACE: CATALOG LOGIC ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

# --- 3. MARKETPLACE: TRANSACTION LOGIC (POST Order) ---
@api_view(['POST'])
@authentication_classes([]) # Added to ensure Frontend can post without CSRF issues
@permission_classes([AllowAny])
def create_order(request):
    data = request.data
    try:
        new_order = Order.objects.create(
            user_id=data.get('userId'),
            total_price=data.get('total'),
            status='Pending' 
        )

        order_items_data = [] 
        for item in data.get('items', []):
            product = Product.objects.get(id=item['id'])
            OrderItem.objects.create(
                order=new_order,
                product=product,
                quantity=item.get('quantity', 1),
                price_at_purchase=product.price
            )
            order_items_data.append({
                "name": product.name,
                "price": float(product.price),
                "quantity": item.get('quantity', 1)
            })

        invoice_payload = {
            "order_id": new_order.id,
            "total_amount": float(data.get('total')),
            "items": order_items_data,
            "user_id": data.get('userId')
        }
        trigger_invoice_generation.delay(invoice_payload)

        return Response({
            "status": "Accepted",
            "message": "Order placed!",
            "id": new_order.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# --- 4. MARKETPLACE: ORDER DETAIL (GET Order for FastAPI) ---
@api_view(['GET'])
@authentication_classes([]) # CRITICAL: This is the primary fix for the 400 error
@permission_classes([AllowAny])
def get_order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order=order)
        
        items_list = []
        for item in items:
            items_list.append({
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price_at_purchase": str(item.price_at_purchase)
            })

        return Response({
            "id": order.id,
            "total_price": str(order.total_price),
            "user_id": order.user_id,
            "items": items_list
        })
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)