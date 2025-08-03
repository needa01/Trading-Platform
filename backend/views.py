from django.shortcuts import render

# Create your views here.
# from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Orders, Trades

@login_required
def staff_order_book(request):
    buy_orders = Orders.objects.filter(type='buy', status__in=['pending', 'partial']).order_by('-price')
    sell_orders = Orders.objects.filter(type='sell', status__in=['pending', 'partial']).order_by('price')
    return render(request, 'backend/order_book.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
    })

@login_required
def staff_trade_history(request):
    trades = Trades.objects.all().order_by('-traded_at')[:100]
    return render(request, 'backend/trade_history.html', {
        'trades': trades,
    })