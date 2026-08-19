from django.urls import path
from . import views

urlpatterns = [
    path('', views.portal_hub_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('distributor-login/', views.distributor_login_view, name='distributor_login'),
    path('distributor-register/', views.distributor_register_view, name='distributor_register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('api/login/', views.api_login_view, name='api_login'),
    path('api/request-otp/', views.api_request_otp_view, name='api_request_otp'),
    path('api/verify-otp/', views.api_verify_otp_view, name='api_verify_otp'),
]
