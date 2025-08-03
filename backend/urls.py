from django.urls import include, path
from . import views

urlpatterns = [
    path('orders/', views.staff_order_book, name='staff_order_book'),
    path('trade-history/', views.staff_trade_history, name='staff_trade_history'),
    
]