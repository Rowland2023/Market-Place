from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
#from . import views  # Ensure this imports your views.py
from super_mart import views 

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This includes the ProductViewSet from your router
    path('api/', include(router.urls)),
    
    # --- AUTH APIs ---
    path('api/register/', views.register_user, name='register'),
    path('api/login/', views.login_user, name='login'), # Added this to fix the 404
    
    # --- HRM API ---
    path('api/employees/<str:employee_id>/', views.employee_detail_api),
    
    # --- MARKETPLACE APIs ---
    path('api/orders/', views.order_list, name='order-list'), 
    path('api/orders/<int:order_id>/', views.get_order_detail, name='order-detail'),
]


# Ensure these imports are at the to

if settings.DEBUG:
    # This serves files from your STATICFILES_DIRS (your actual 'static' folder)
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    
    # This serves the Media files (uploads)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)