from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.db.models import Q

# Create your views here.
# from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from backend.engine import match_order
from .models import Currency, Market, Orders, Portfolio, Trades, Wallet

@login_required
def staff_order_book(request):
    buy_orders = Orders.objects.filter(type='buy', status__in=['pending', 'partial']).order_by('-price')
    sell_orders = Orders.objects.filter(type='sell', status__in=['pending', 'partial']).order_by('price')
    return render(request, 'backend/order_book.html', {
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
    })

@login_required
def staff_trades(request):
    trades = Trades.objects.all().order_by('-traded_at')[:100]
    return render(request, 'backend/trade_history.html', {
        'trades': trades,
    })
    
@login_required
@transaction.atomic
def place_order(request):
    if request.method == "POST":
        user = request.user
        order_type = request.POST.get("type")  # 'buy' or 'sell'
        price = Decimal(request.POST.get("price"))
        quantity = Decimal(request.POST.get("quantity"))

        # ✅ Convert base and quote from ID to model instance
        try:
            base = Currency.objects.get(id=request.POST.get("base_currency"))
            quote = Currency.objects.get(id=request.POST.get("quote_currency"))
        except Currency.DoesNotExist:
            return JsonResponse({"error": "Invalid base or quote currency"}, status=400)

        wallet = Wallet.objects.select_for_update().get(user=user, crypto__symbol=quote.symbol if order_type == "buy" else base.symbol)

        if order_type == "buy":
            total_cost = price * quantity
            if wallet.available_balance < total_cost:
                return JsonResponse({"error": "Insufficient funds"}, status=400)
            wallet.available_balance -= total_cost
            wallet.locked_balance += total_cost
            wallet.save()

        elif order_type == "sell":
            try:
                # ✅ Use base.symbol because Portfolio stores asset_name as CharField
                portfolio = Portfolio.objects.select_for_update().get(user=user, asset__symbol=base.symbol)
            except Portfolio.DoesNotExist:
                return JsonResponse({"error": "No holdings for asset"}, status=400)
            if portfolio.quantity < quantity:
                return JsonResponse({"error": "Insufficient asset quantity"}, status=400)
            portfolio.quantity -= quantity  # Locking virtually
            portfolio.save()

        order = Orders.objects.create(
            user=user,
            type=order_type,
            price=price,
            quantity=quantity,
            remaining_quantity=quantity,
            base_currency=base,
            quote_currency=quote,
            status="pending"
        )

        # Call matching engine
        match_order(order)

        return JsonResponse({"message": "Order placed successfully"})

    # GET request
    cryptos = Currency.objects.all()
    return render(request, "backend/place_order.html", {"cryptos": cryptos})


@login_required
def portfolio_view(request):
    user = request.user
    portfolio = Portfolio.objects.filter(user=user)

    # Add current LTP value for each asset
    enriched_portfolio = []
    for p in portfolio:
        try:
            ltp = Market.objects.get(symbol=p.asset__name).last_traded_price
        except Market.DoesNotExist:
            ltp = 0
        current_value = p.quantity * ltp
        enriched_portfolio.append({
            "asset_name": p.asset__symbol,
            "quantity": p.quantity,
            "avg_price": p.avg_purchase_price,
            "ltp": ltp,
            "current_value": current_value
        })

    return render(request, "backend/portfolio.html", {"portfolio": enriched_portfolio})


@login_required
def my_trades_view(request):
    user = request.user
    trades = Trades.objects.filter(Q(buyer=user) | Q(seller=user)).order_by("-traded_at")
    return render(request, "backend/my_trades.html", {"trades": trades})

@login_required
def my_orders_view(request):
    orders = Orders.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "backend/my_orders.html", {"orders": orders})

def order_book_view(request):
    buy_orders = Orders.objects.filter(
        status__in=["pending", "partial"], type="buy"
    ).order_by("-price", "created_at")

    sell_orders = Orders.objects.filter(
        status__in=["pending", "partial"], type="sell"
    ).order_by("price", "created_at")

    return render(request, "backend/order_book.html", {
        "buy_orders": buy_orders,
        "sell_orders": sell_orders
    })
    

def ltp_view(request):
    ltps = Market.objects.all().order_by("symbol")
    return render(request, "backend/ltp.html", {"ltps": ltps})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Orders, id=order_id, user=request.user)
    
    if order.status in ['filled', 'cancelled']:
        return redirect('order_book')  # can't cancel already executed orders

    # Refund locked amount (quote currency for BUY, base currency for SELL)
    refund_amount = order.remaining_quantity * order.price if order.type == 'buy' else order.remaining_quantity

    if order.type == 'buy':
        request.user.wallet.locked_balance += refund_amount
        request.user.wallet.available_balance += refund_amount
    else:
        request.user.wallet.available_balance += refund_amount
        request.user.wallet.locked_balance -= refund_amount

    request.user.wallet.save()

    order.status = 'cancelled'
    order.remaining_quantity = 0
    order.save()

    return redirect('order_book')

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Orders, id=order_id, user=request.user)
    
    if order.status in ['filled', 'cancelled']:
        return redirect('order_book')  # can't cancel already executed orders

    # Refund locked amount (quote currency for BUY, base currency for SELL)
    refund_amount = order.remaining_quantity * order.price if order.type == 'buy' else order.remaining_quantity

    if order.type == 'buy':
        request.user.wallet.locked_balance += refund_amount
        request.user.wallet.available_balance += refund_amount
    else:
        request.user.wallet.available_balance += refund_amount
        request.user.wallet.locked_balance -= refund_amount

    request.user.wallet.save()

    order.status = 'cancelled'
    order.remaining_quantity = 0
    order.save()

    return redirect('order_book')