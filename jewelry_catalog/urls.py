from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('gallery/', include('gallery.urls')),
    path('accounts/', include('accounts.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('tiendas/', include('partners.urls')),


    # API URLs
    path('api/products/', include('products.api_urls')),
    path('api/orders/', include('orders.api_urls')),

    # Monitoring URLs
    path('health/', views.health_check, name='health_check'),
    path('metrics/', views.metrics, name='metrics'),
    path('alerts/', views.alerts, name='alerts'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)