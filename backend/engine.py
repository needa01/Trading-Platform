from .models import Orders, Trades, Wallet, Portfolio, Market
from decimal import Decimal
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

def broadcast_orderbook_update(ltp, asset):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "orderbook",
        {
            "type": "send_orderbook",
            "data": {
                "ltp": str(ltp),
                "asset": asset,
                "time": timezone.now().isoformat()
            }
        }
    )

def send_user_notification(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_notification",
            "message": message
        }
    )

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

    else:  # SELL
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

        trade_qty = min(order.remaining_quantity, match.remaining_quantity)
        execution_price = match.price  # market chooses maker's price

        # Buyer/Seller identification
        buy_order = order if order.type == 'buy' else match
        sell_order = order if order.type == 'sell' else match
        buyer = buy_order.user
        seller = sell_order.user

        # Wallet adjustments
        total_trade_amount = trade_qty * execution_price
        buyer_wallet = Wallet.objects.select_for_update().get(user=buyer)
        seller_wallet = Wallet.objects.select_for_update().get(user=seller)

        buyer_wallet.locked_balance -= total_trade_amount
        seller_wallet.available_balance += total_trade_amount
        buyer_wallet.save()
        seller_wallet.save()

        # Portfolio Updates
        portfolio, _ = Portfolio.objects.get_or_create(user=buyer, asset_name=base)
        portfolio.quantity += trade_qty
        # Update average purchase price
        if portfolio.avg_purchase_price == 0:
            portfolio.avg_purchase_price = execution_price
        else:
            portfolio.avg_purchase_price = (
                (portfolio.avg_purchase_price * (portfolio.quantity - trade_qty)) + (execution_price * trade_qty)
            ) / portfolio.quantity
        portfolio.save()

        # Record trade
        Trades.objects.create(
            buy_order=buy_order,
            sell_order=sell_order,
            price=execution_price,
            quantity=trade_qty,
            buyer=buyer,
            seller=seller
        )

        # Update remaining quantity and status
        for o in [order, match]:
            o.remaining_quantity -= trade_qty
            if o.remaining_quantity == 0:
                o.status = 'filled'
            else:
                o.status = 'partial'
            o.save()

        # Update LTP
        Market.objects.filter(symbol=base).update(last_traded_price=execution_price)
          # Real-time WebSocket broadcast
        broadcast_orderbook_update(execution_price, f"{base}/{quote}")

        # User-specific notifications
        send_user_notification(buyer.id, f"✅ Buy matched: {trade_qty} {base} @ {execution_price}")
        send_user_notification(seller.id, f"✅ Sell matched: {trade_qty} {base} @ {execution_price}")