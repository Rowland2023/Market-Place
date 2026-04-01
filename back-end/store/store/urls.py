from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import everything from your app's views clearly
from super_mart import views 

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Standard CRUD (Products)
    path('api/', include(router.urls)),
    
    # 2. The Bridge for FastAPI (Employee Data)
    # This MUST match the URL FastAPI is calling
    path('api/employees/<str:employee_id>/', views.employee_detail_api, name='employee-detail'),
    
    # 3. The Order Logic (Function-based view)
    path('api/orders/', views.create_order, name='create-order'),
]