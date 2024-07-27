from django.db import models
from adminapp.models import CustomUser,Product
import uuid

from django.conf import settings
from decimal import Decimal
# Create your models here.


class CheckoutAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=25,blank=True)
    phone = models.CharField(max_length=10,blank=True)
    phone_alternate = models.CharField(max_length=10,blank=True)
    apartment_address = models.CharField(max_length=255,null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=10, choices=[('Home', 'HOME'), ('Office', 'OFFICE')])
    default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.apartment_address}"

    class Meta:
        verbose_name_plural = "Checkout Addresses"
        constraints = [
            models.UniqueConstraint(fields=['user', 'address_type', 'default'], 
                condition=models.Q(default=True),
                name='unique_default_address_per_type')
        ]

class OrderAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    phone = models.CharField(max_length=10)
    phone_alternate = models.CharField(max_length=10, blank=True)
    apartment_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=10, choices=[('Home', 'HOME'), ('Office', 'OFFICE')])

    def __str__(self):
        return f"{self.name} - {self.apartment_address}"

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(OrderAddress, on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True) 
    payment_id = models.CharField(max_length=100, blank=True, null=True) 
    payment_method = models.CharField(max_length=20, choices=[
        ('UPI_PAYMENTS', 'UPI payments'),
        ('WALLET', 'Wallet'),
        ('COD', 'Cash on Delivery')
    ], default='COD')

   
    def __str__(self):
        return f"Order by {self.user.username} to {self.shipping_address.name}"
    
    
   
    
    
class OrderItem(models.Model):
    order_number = models.CharField(max_length=20, unique=True, editable=False,null=True)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    offer = models.PositiveBigIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned')
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    payment_status = models.CharField(max_length=20, choices=[
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
    ], default='UNPAID')

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.user.username}"
    
    def can_transition_to(self, new_status):
        if self.status == 'PENDING':
            return new_status in ['PROCESSING', 'CANCELLED']
        elif self.status == 'PROCESSING':
            return new_status in ['SHIPPED', 'CANCELLED']
        elif self.status == 'SHIPPED':
            return new_status in ['DELIVERED', 'RETURNED']
        elif self.status == 'DELIVERED':
            return False
        return False
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        return str(uuid.uuid4().hex[:10].upper())
    
    @property
    def subtotal(self):
        return self.quantity * self.price

    


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    def add_funds(self, amount):
        self.balance += Decimal(str(amount))
        self.save()

    def deduct_funds(self, amount):
        if self.balance >= Decimal(str(amount)):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.user.username}"
    



class ReturnedProduct(models.Model):
    RETURN_REASONS = [
        ('defective', 'Product is defective'),
        ('wrong_item', 'Received wrong item'),
        ('not_as_described', 'Item not as described'),
        ('no_longer_needed', 'No longer needed'),
        ('other', 'Other'),
    ]

    RETURN_STATUSES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        # ('completed', 'Completed'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='returns')
    order_item = models.ForeignKey('OrderItem', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=RETURN_STATUSES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Return #{self.id} - {self.order_item.product.name} from Order {self.order_item.order_number}"

    class Meta:
        ordering = ['-requested_at']


