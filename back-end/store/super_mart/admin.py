from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
# Ensure all models are imported correctly
from .models import Employee, Attendance, Payroll, PerformanceReview, Product, Order, OrderItem

# --- 1. Global Site Branding ---
admin.site.site_header = "Lagos Tech Hub: Market-Place & HRM"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Command Center"

# --- 2. Product Management (Marketplace) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'view_product_image')
    list_filter = ('category',)
    search_fields = ('name',)
    
    def thumbnail(self, obj):
        if obj.image_path:
            return format_html('<img src="/static/{}" style="width: 50px; height: 50px; border-radius: 4px;" />', obj.image_path)
        return "No Image"
    thumbnail.short_description = "Preview"

    def view_product_image(self, obj):
        if obj.image_path:
             return format_html('<code style="color: #d63384;">{}</code>', obj.image_path)
        return "No Path Set"
    view_product_image.short_description = "Storage Path"

# --- 3. Employee & HRM Management ---
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    readonly_fields = ('date', 'status')
    can_delete = False

class PayrollInline(admin.StackedInline):
    model = Payroll
    extra = 0
    classes = ('collapse',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'department', 'position', 'get_status_badge')
    list_filter = ('department', 'is_active', 'position')
    search_fields = ('first_name', 'last_name', 'employee_id')
    inlines = [AttendanceInline, PayrollInline]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_status_badge(self, obj):
        color = "green" if obj.is_active else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                           color, "ACTIVE" if obj.is_active else "INACTIVE")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status')
    list_filter = ('date', 'status')

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period', 'amount', 'is_paid', 'download_payslip')
    
    def download_payslip(self, obj):
        emp_id = str(obj.employee.employee_id).strip()
        fastapi_url = f"http://localhost:8001/api/invoices/generate?user_id={emp_id}"
        return format_html('<a class="button" href="{}" target="_blank" style="background-color: #447e9b; color: white; padding: 5px; border-radius: 4px; text-decoration: none;">PDF</a>', fastapi_url)

# --- 4. Order & Tracking Management (With Dashboard Logic) ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Added 'created_at' and 'download_receipt' to the table
    list_display = ('id', 'user_id', 'total_price', 'status', 'created_at', 'download_receipt')
    list_editable = ('status',) 
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user_id')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

    def download_receipt(self, obj):
        fastapi_url = f"http://localhost:8001/api/invoices/generate?order_id={obj.id}"
        return format_html('<a class="button" href="{}" target="_blank" style="background-color: #2e7d32; color: white; padding: 5px; border-radius: 4px; text-decoration: none;">Receipt</a>', fastapi_url)
    download_receipt.short_description = "Action"

    # --- DASHBOARD LOGIC ---
    def changelist_view(self, request, extra_context=None):
        # Calculate Total Revenue from Paid orders
        total_revenue = Order.objects.filter(status="Paid").aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Get 5 Latest Transactions
        latest_transactions = Order.objects.all().order_by('-created_at')[:5]

        # Get 5 Top Selling Products (Aggregating OrderItem quantities)
        top_products = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).filter(total_sold__gt=0).order_by('-total_sold')[:5]

        extra_context = extra_context or {}
        extra_context['total_revenue'] = total_revenue
        extra_context['latest_transactions'] = latest_transactions
        extra_context['top_products'] = top_products
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')