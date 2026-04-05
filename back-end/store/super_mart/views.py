from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product, Order, OrderItem, Employee, Payroll
from .serializers import ProductSerializer, OrderSerializer 
from .tasks import trigger_invoice_generation 

# --- 1. AUTH: REGISTRATION & LOGIN ---

@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def register_user(request):
    data = request.data
    try:
        if User.objects.filter(username=data.get('username')).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password')
        )
        return Response({
            "message": "User created successfully",
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def login_user(request):
    """
    Verifies credentials and returns user details.
    """
    data = request.data
    username = data.get('username')
    password = data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        return Response({
            "message": "Login successful",
            "user_id": user.id,
            "email": user.email
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid Email or Password"}, status=status.HTTP_401_UNAUTHORIZED)

# --- 2. HRM: EMPLOYEE DATA API ---
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([AllowAny]) 
def employee_detail_api(request, employee_id):
    try:
        emp = Employee.objects.filter(employee_id=employee_id).first()
        if not emp and str(employee_id).isdigit():
            emp = Employee.objects.filter(employee_id=str(employee_id).lstrip('0')).first()
            
        if not emp:
            return Response({"error": f"Employee {employee_id} not found"}, status=404)
        
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

# --- 3. MARKETPLACE: CATALOG ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

# --- 4. MARKETPLACE: UNIFIED ORDER API ---
@api_view(['GET', 'POST'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def order_list(request):
    if request.method == 'GET':
        user_id = request.query_params.get('userId')
        orders = Order.objects.all().order_by('-id')
        if user_id:
            orders = orders.filter(user_id=user_id)
            
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        data = request.data
        try:
            new_order = Order.objects.create(
                user_id=data.get('userId', 'guest_001'),
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

# --- 5. MARKETPLACE: ORDER DETAIL ---
@api_view(['GET'])
@authentication_classes([]) 
@permission_classes([AllowAny])
def get_order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order=order)
        items_list = [{"product_name": i.product.name, "quantity": i.quantity, "price": str(i.price_at_purchase)} for i in items]
        return Response({"id": order.id, "total": str(order.total_price), "user_id": order.user_id, "items": items_list, "status": getattr(order, 'status', 'Processing')})
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)