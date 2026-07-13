# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Template views
    path('', views.product_list, name='product_list'),

    # Product management views (require login) - BEFORE slug detail to avoid conflicts
    path('create/', views.product_create, name='product_create'),
    path('<int:product_id>/update/', views.product_update, name='product_update'),
    path('<int:product_id>/delete/', views.product_delete, name='product_delete'),

    # Category views - prefixed to avoid conflicts with product detail slugs
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),

    # Product detail - AFTER management routes so /create/, etc. take precedence
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # API views
    path('list/', views.ProductListAPIView.as_view(), name='api_product_list'),
    path('detail/<slug:slug>/', views.ProductDetailAPIView.as_view(), name='api_product_detail'),
    path('categories/list/', views.CategoryListAPIView.as_view(), name='api_category_list'),
    path('categories/detail/<int:pk>/', views.CategoryDetailAPIView.as_view(), name='api_category_detail'),
    path('featured/', views.featured_products_api, name='api_featured_products'),
    path('category/<slug:category_slug>/', views.products_by_category_api, name='api_products_by_category'),
]
