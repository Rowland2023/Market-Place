from rest_framework import serializers
from .models import (
    Product, Order, OrderItem, 
    Employee, Attendance, Payroll, PerformanceReview, ProductImage
)

# --- 1. MARKETPLACE & INVENTORY SERIALIZERS ---

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image_path', 'alt_text']

class ProductSerializer(serializers.ModelSerializer):
    # This pulls the related images into the product JSON
    # 'source=images' maps to the related_name in your ProductImage model
    additional_images = ProductImageSerializer(many=True, read_only=True, source='images')

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'image_path', 'additional_images']

class OrderItemSerializer(serializers.ModelSerializer):
    # This pulls the product name into the order item for the PDF/Frontend
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    # This allows you to see all items inside an order (Nested Serializer)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user_id', 'created_at', 'total_price', 'status', 'items']


# --- 2. HRM & EMPLOYEE SERIALIZERS ---

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = '__all__'

class PerformanceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReview
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    # Nested relations to see history in the employee profile
    payrolls = PayrollSerializer(many=True, read_only=True)
    attendance = AttendanceSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'first_name', 'last_name', 
            'email', 'department', 'position', 'salary', 
            'is_active', 'date_joined', 'payrolls', 'attendance'
        ]