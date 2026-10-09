from django.urls import path
from . import views

urlpatterns = [
    # Product HTML UI Views
    path('', views.product_list_view, name='product_list'),
    path('<int:pk>/', views.product_detail_view, name='product_detail'),
    path('add/', views.product_create_view, name='product_create'),
    path('<int:pk>/edit/', views.product_update_view, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('<int:pk>/toggle-status/', views.product_toggle_status_view, name='product_toggle_status'),

    # Product REST API Endpoints
    path('api/products/', views.api_product_list_create, name='api_product_list'),
    path('api/products/<int:pk>/', views.api_product_detail, name='api_product_detail'),
]
