from django.urls import path
from . import views

urlpatterns = [
    # Web UI Customer Routes
    path('', views.customer_list_view, name='customer_list'),
    path('add/', views.customer_create_view, name='customer_create'),
    path('<int:pk>/', views.customer_detail_view, name='customer_detail'),
    path('<int:pk>/edit/', views.customer_update_view, name='customer_update'),
    path('<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),
    path('<int:pk>/toggle-status/', views.customer_toggle_status_view, name='customer_toggle_status'),

    # REST API Routes
    path('api/customers/', views.api_customer_list_create, name='api_customer_list_create'),
    path('api/customers/<int:pk>/', views.api_customer_detail, name='api_customer_detail'),
]
