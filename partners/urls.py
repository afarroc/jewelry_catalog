# partners/urls.py
from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    path('', views.PartnerListView.as_view(), name='list'),
    path('<slug:slug>/', views.PartnerDetailView.as_view(), name='detail'),
]
