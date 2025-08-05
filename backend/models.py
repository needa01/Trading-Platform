from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=255, null=True, blank=True) 
    username = models.CharField(max_length=255, unique=True, blank=False, null=False)
    title = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True) 
    created_at = models.DateTimeField(auto_now_add=True,blank=False,null=False)
    class Meta:
        verbose_name_plural = "User"

from django.db import models
from django.conf import settings

# ---------------------
# 1. Wallet Table
# ---------------------

class Crypto(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, default='BTC')
    
    def __str__(self):
        return self.symbol
    
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    crypto=models.ForeignKey(Crypto,on_delete=models.CASCADE, null=True)
    available_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    class Meta:
        unique_together = ('user', 'crypto')
    def __str__(self):
        return f"{self.user.username}'s Wallet"

# ---------------------
# 2. Orders Table
# ---------------------
class Orders(models.Model):
    BUY = 'buy'
    SELL = 'sell'
    ORDER_TYPE_CHOICES = [(BUY, 'Buy'), (SELL, 'Sell')]

    PENDING = 'pending'
    PARTIAL = 'partial'
    FILLED = 'filled'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PARTIAL, 'Partially Filled'),
        (FILLED, 'Filled'),
        (CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    base_currency = models.ForeignKey(Crypto, on_delete=models.CASCADE, related_name='base',null=True)   # e.g. BTC
    quote_currency = models.ForeignKey(Crypto, on_delete=models.CASCADE, related_name='quote',null=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type.upper()} {self.quantity} {self.base_currency}"

# ---------------------
# 3. Trades Table
# ---------------------
class Trades(models.Model):
    buy_order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='buy_trades')
    sell_order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='sell_trades')
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_user_trades')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sell_user_trades')
    traded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trade: {self.quantity} {self.buy_order.base_currency} @ {self.price}"

# ---------------------
# 4. Portfolio Table
# ---------------------
class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio')
    asset_name = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    avg_purchase_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    class Meta:
        unique_together = ('user', 'asset_name')

    def __str__(self):
        return f"{self.user.username} - {self.asset_name}: {self.quantity}"

# ---------------------
# 5. Market Table (LTP)
# ---------------------
class Market(models.Model):
    name = models.CharField(max_length=50, default='BITCOIN')         # e.g., Bitcoin
    symbol = models.CharField(max_length=10, default='BTC')  # e.g., BTC
    last_traded_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    last_updated = models.DateTimeField(auto_now=True)  # ✅ add this

    def __str__(self):
        return f"{self.name} - LTP: {self.last_traded_price}"

# ---------------------
# 6. WalletTransaction Table (Optional but Useful)
# ---------------------
class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    type = models.CharField(max_length=10, choices=[("CREDIT", "CREDIT"), ("DEBIT", "DEBIT")])
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.type} {self.amount}"
