from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('', views.invoice_list_view, name='invoice_list'),
    path('<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('create/', views.invoice_create_view, name='invoice_create'),

    # REST API JSON Endpoints
    path('api/', views.api_invoice_list, name='api_invoice_list'),
    path('api/<int:pk>/', views.api_invoice_detail, name='api_invoice_detail'),
    path('api/customers/<int:pk>/', views.api_customer_detail, name='api_invoice_customer_detail'),
    path('api/products/<int:pk>/', views.api_product_detail, name='api_invoice_product_detail'),
]
