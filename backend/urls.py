from django.urls import include, path
from . import views

urlpatterns = [
    path('orders/', views.staff_order_book, name='staff_order_book'),
    path('trade-history/', views.staff_trades, name='staff_trade_history'),
    path("place-order/", views.place_order, name="place_order"),
    path("portfolio/", views.portfolio_view, name="portfolio"),
    path("my-trades/", views.my_trades_view, name="my_trades"),
    path("my-orders/", views.my_orders_view, name="my_orders"),
    path("order-book/", views.order_book_view, name="order_book"),
    path("ltp/", views.ltp_view, name="ltp"),
    path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
]