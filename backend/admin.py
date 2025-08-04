from django.contrib import admin

# Register your models here.
from .models import CustomUser, Market, Portfolio, Wallet

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'fullname', 'is_staff']
    
@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'last_traded_price']
    search_fields = ['name', 'symbol']
    


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user','crypto', 'available_balance', 'locked_balance']
    actions = ['add_funds']

    def add_funds(self, request, queryset):
        for wallet in queryset:
            wallet.available_balance += 10000  # for example
            wallet.save()
        self.message_user(request, "Added 10,000 units to selected wallets.")

    add_funds.short_description = "Add 10,000 to available balance"
    
@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset_name', 'quantity', 'avg_purchase_price')
    search_fields = ('user__username', 'asset_name')
    list_filter = ('asset_name',)
    ordering = ('user__username', 'asset_name')

    def total_value(self):
        return self.quantity * self.avg_purchase_price
    total_value.short_description = 'Total Value'