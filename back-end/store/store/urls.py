from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from super_mart import views 

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/employees/<str:employee_id>/', views.employee_detail_api),
    path('api/orders/', views.create_order), 
    path('api/orders/<int:order_id>/', views.get_order_detail, name='order-detail'),
]