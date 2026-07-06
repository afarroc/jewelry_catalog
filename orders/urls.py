from django.urls import path
from . import views
from .webhooks import stripe_webhook

app_name = 'orders'

urlpatterns = [
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<int:order_id>/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('create-order/', views.create_order_ajax, name='create_order_ajax'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
    path('detail/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('invoice/<int:order_id>/', views.OrderInvoiceView.as_view(), name='order_invoice'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('terms-and-conditions/', views.TermsAndConditionsView.as_view(), name='terms'),

    path('list/', views.OrderListAPIView.as_view(), name='api_order_list'),
    path('detail/<str:order_number>/', views.OrderDetailAPIView.as_view(), name='api_order_detail'),
    path('cancel/<str:order_number>/', views.cancel_order_api, name='api_cancel_order'),
    path('history/', views.order_history_api, name='api_order_history'),
]
