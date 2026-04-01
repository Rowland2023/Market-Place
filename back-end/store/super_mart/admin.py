from django.contrib import admin
from django.utils.html import format_html
from .models import Employee, Attendance, Payroll, PerformanceReview, Product

# --- 1. Global Site Branding ---
admin.site.site_header = "Lagos Tech Hub: Market-Place & HRM"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Command Center"

# --- 2. Product Management (Marketplace Side) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'view_product_image')
    list_filter = ('category',)
    search_fields = ('name',)
    
    def view_product_image(self, obj):
        if hasattr(obj, 'image_path') and obj.image_path:
             return format_html('<span style="font-family: monospace;">{}</span>', obj.image_path)
        return "No Path Set"
    view_product_image.short_description = "Storage Path"

# --- 3. Employee Management (HRM Side) ---

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
    
    fieldsets = (
        ('Identity', {
            'fields': (('first_name', 'last_name'), 'employee_id', 'email')
        }),
        ('Professional Details', {
            'fields': ('department', 'position', 'salary', 'is_active')
        }),
    )
    
    inlines = [AttendanceInline, PayrollInline]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Employee Name"

    def get_status_badge(self, obj):
        color = "green" if obj.is_active else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                           color, "ACTIVE" if obj.is_active else "INACTIVE")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'status')
    list_filter = ('date', 'status', 'employee__department')
    date_hierarchy = 'date'

@admin.register(PerformanceReview)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'review_date', 'rating', 'reviewer')
    list_editable = ('rating',)
    list_filter = ('rating', 'review_date')

# --- 4. Payroll Management (The "Money" Side) ---
@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period', 'amount', 'is_paid', 'download_payslip')
    list_filter = ('is_paid', 'pay_period')
    search_fields = ('employee__last_name', 'pay_period')

    def download_payslip(self, obj):
        # 1. Ensure the ID is a clean string
        emp_id = str(obj.employee.employee_id).strip()
        
        # 2. Point to LOCALHOST:8001 (Your browser clicks this)
        fastapi_url = f"http://localhost:8001/api/invoices/generate?user_id={emp_id}"
        
        return format_html(
            '<a class="button" href="{}" target="_blank" '
            'style="background-color: #447e9b; color: white; padding: 5px 10px; '
            'border-radius: 4px; text-decoration: none;">Download PDF</a>', 
            fastapi_url
        )
    
    download_payslip.short_description = 'Payslip Action'