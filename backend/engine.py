
from .models import Orders, Trades, Wallet, Portfolio, Market
from decimal import Decimal
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

@transaction.atomic
def match_order(order):
    user = order.user
    base = order.base_currency
    quote = order.quote_currency

    if order.type == 'buy':
        opposite_orders = Orders.objects.select_for_update().filter(
            type='sell',
            base_currency=base,
            quote_currency=quote,
            status__in=['pending', 'partial'],
            price__lte=order.price
        ).order_by('price', 'created_at')
    else:
        opposite_orders = Orders.objects.select_for_update().filter(
            type='buy',
            base_currency=base,
            quote_currency=quote,
            status__in=['pending', 'partial'],
            price__gte=order.price
        ).order_by('-price', 'created_at')

    for match in opposite_orders:
        if order.remaining_quantity <= 0:
            break

        if match.user == order.user:
            continue

        trade_qty = min(order.remaining_quantity, match.remaining_quantity)
        execution_price = match.price  # Maker's price
        total_trade_amount = trade_qty * execution_price

        # Identify buyer/seller
        buy_order = order if order.type == 'buy' else match
        sell_order = order if order.type == 'sell' else match
        buyer = buy_order.user
        seller = sell_order.user

        # 🔹 Wallet updates for quote currency
        buyer_quote_wallet = Wallet.objects.select_for_update().get(user=buyer, crypto=quote)
        seller_quote_wallet = Wallet.objects.select_for_update().get(user=seller, crypto=quote)

        buyer_quote_wallet.locked_balance -= total_trade_amount
        seller_quote_wallet.available_balance += total_trade_amount
        buyer_quote_wallet.save()
        seller_quote_wallet.save()

        # 🔹 Wallet updates for base currency
        buyer_base_wallet, _ = Wallet.objects.select_for_update().get_or_create(user=buyer, crypto=base)
        buyer_base_wallet.available_balance += trade_qty
        buyer_base_wallet.save()

        seller_base_wallet, _ = Wallet.objects.select_for_update().get_or_create(user=seller, crypto=base)
        seller_base_wallet.locked_balance -= trade_qty
        seller_base_wallet.save()

        # 🔹 Portfolio update for buyer
        buyer_portfolio, _ = Portfolio.objects.select_for_update().get_or_create(user=buyer, asset=base)
        old_total = buyer_portfolio.quantity * buyer_portfolio.avg_purchase_price
        buyer_portfolio.quantity += trade_qty
        buyer_portfolio.avg_purchase_price = (
            (old_total + trade_qty * execution_price) / buyer_portfolio.quantity
        )
        buyer_portfolio.save()

        # 🔹 Portfolio update for seller (decrease sold quantity)
        seller_portfolio, _ = Portfolio.objects.select_for_update().get_or_create(user=seller, asset=base)
        seller_portfolio.quantity -= trade_qty
        if seller_portfolio.quantity < 0:
            seller_portfolio.quantity = 0
        seller_portfolio.save()

        # 🔹 Record trade
        Trades.objects.create(
            buy_order=buy_order,
            sell_order=sell_order,
            price=execution_price,
            quantity=trade_qty,
            buyer=buyer,
            seller=seller
        )

        # 🔹 Update order statuses
        for o in [order, match]:
            o.remaining_quantity -= trade_qty
            o.status = 'filled' if o.remaining_quantity == 0 else 'partial'
            o.save()

        # 🔹 Update LTP
        Market.objects.filter(symbol=base).update(last_traded_price=execution_price)

        # 🔹 WebSocket Updates
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "orderbook",
            {
                "type": "send_orderbook",
                "data": {
                    "ltp": str(execution_price),
                    "asset": f"{base}/{quote}",
                    "time": timezone.now().isoformat()
                }
            }
        )

        async_to_sync(channel_layer.group_send)(
            "tradehistory",
            {
                "type": "send_trade",
                "data": {
                    "price": str(execution_price),
                    "quantity": str(trade_qty),
                    "asset": f"{base}/{quote}",
                    "time": timezone.now().isoformat()
                }
            }
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{buyer.id}",
            {
                "type": "send_portfolio",
                "data": {
                    "asset": base.symbol,
                    "quantity": str(buyer_portfolio.quantity),
                    "avg_price": str(buyer_portfolio.avg_purchase_price)
                }
            }
        )