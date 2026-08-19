from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.distributor_register_view, name='distributor_register'),
]
