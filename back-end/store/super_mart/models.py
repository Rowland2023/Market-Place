from django.db import models

# --- 1. MARKETPLACE & INVENTORY ---

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food & Drinks'),
        ('electronics', 'Electronics'),
        ('office', 'Office Supplies'),
        ('style&fashion', 'Style & Fashion'),
        ('home', 'Home & Garden'),  
        ('toys', 'Toys & Games '),
        ('health', 'Health & Beauty'),
        ('sports', 'Sports & Outdoors'),
        ('automotive', 'Automotive'),
        ('books', 'Books & Media'),
        ('miscKitchen', 'Kitchen & Dining'),
        ('sex-toys', 'Sex-Toys'),
        ('rent-house','House-Rent'),
        ('car-sales','Car-Sales'),
        ('kitchen-items','Kitchen-Items'),
    ]
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    # Architect's Tip: Using CharField for pathing is great for Docker/S3 flexibility
    image_path = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image_path = models.CharField(max_length=255)  # e.g., 'images/products/detail_1.jpg'
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class Order(models.Model):
    # Define the professional stages of your order
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user_id = models.CharField(max_length=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    # Add 'choices' here to trigger the dropdown in Admin
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"
class OrderItem(models.Model):
    """The 'Through' model linking Products to Orders and tracking historical prices."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # Snapshot the price to protect against future price changes in the Product table
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id})"


# --- 2. EMPLOYEE MANAGEMENT (HRM) ---

class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late')])

    def __str__(self):
        return f"{self.employee.last_name} - {self.date} ({self.status})"

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    pay_period = models.CharField(max_length=50) # e.g., "March 2026"
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Payroll {self.pay_period} - {self.employee.last_name}"

class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews')
    review_date = models.DateField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    reviewer = models.CharField(max_length=100)

    def __str__(self):
        return f"Review {self.review_date} - {self.employee.last_name} ({self.rating}/5)"