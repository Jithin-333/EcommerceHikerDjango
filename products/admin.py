from django.contrib import admin
from products.models import CheckoutAddress, OrderItem, Order,Wallet,WalletTransaction,OrderAddress,ReturnedProduct
# Register your models here.

admin.site.register(CheckoutAddress)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(OrderAddress)
admin.site.register(ReturnedProduct)