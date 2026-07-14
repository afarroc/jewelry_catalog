from django.shortcuts import redirect
from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('', views.gallery_home, name='home'),
    path('images/', views.image_list, name='image_list'),
    path('images/upload/', views.image_upload, name='image_upload'),
    path('images/editor/', views.product_image_editor, name='image_editor'),
    path('images/<int:image_id>/', views.image_detail, name='image_detail'),
    path('images/<int:image_id>/delete/', views.image_delete, name='image_delete'),
    path('images/bulk-delete/', views.image_bulk_delete, name='image_bulk_delete'),
    path('images/diagnostic/', views.s3_diagnostic, name='s3_diagnostic'),
    path('products/create/', lambda req: redirect('products:product_create'), name='product_create'),
]
