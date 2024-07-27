from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Max,Aggregate

import os
from django.conf import settings
from django.utils import timezone
from datetime import timedelta,datetime
from django.core.exceptions import ValidationError
from django.db.models import Sum, F

# Create your models here
from decimal import Decimal


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, phone, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, first_name, last_name, phone, password, **extra_fields)


# models
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=15, blank=True)

    addressOne = models.CharField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    index = models.PositiveIntegerField(editable=False, null=True) 

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'phone']

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            # Get the current highest index and add 1
            max_index = CustomUser.objects.aggregate(Max('index'))['index__max']
            self.index = (max_index or 0) + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        current_index = self.index
        super().delete(*args, **kwargs)
        # Reindex remaining users
        users = CustomUser.objects.filter(index__gt=current_index).order_by('index')
        for user in users:
            user.index -= 1
            user.save()


#=====================Products--and--other--models====================#
class BaseModel(models.Model):
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

class Category(BaseModel):
    name = models.CharField(max_length=100)
  

    def __str__(self):
        return self.name
    

class Variant(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    def get_options(self):
        return self.options.all()
    
class VariantOption(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.variant.name}: {self.value}"

class Image(models.Model):
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image {self.id}"
    
    @property
    def url(self):
        return self.image.url
    
    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    variant_option = models.ForeignKey(VariantOption, on_delete=models.CASCADE,null=True)
    images = models.ManyToManyField(Image, blank=True)
    is_active = models.BooleanField(default=True)
    index = models.PositiveIntegerField(editable=False, null=True)
    is_featured = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.name
    
    @property
    def offer_price(self):
        max_discount = self.get_max_discount_percentage()

        if max_discount > 0:
            discount_amount = (max_discount / Decimal('100')) * self.price
            offer_price = (self.price - discount_amount).quantize(Decimal('0.01'))
            return offer_price

        return self.price

    def get_product_offers(self):
        return self.offer_set.filter(discount_percentage__isnull=False).order_by('-discount_percentage')

    def get_category_offers(self):
        return CategoryOffer.objects.filter(category=self.category).order_by('-discount_percentage')

    def get_max_discount_percentage(self):
        product_offer = self.get_product_offers().first()
        category_offer = self.get_category_offers().first()

        product_discount = Decimal(product_offer.discount_percentage) if product_offer else Decimal('0')
        category_discount = Decimal(category_offer.discount_percentage) if category_offer else Decimal('0')

        return max(product_discount, category_discount)

    def get_discount_percentage(self):
        max_discount = self.get_max_discount_percentage()
        if max_discount > 0:
            return int(max_discount)
        return 0
        
    def save(self, *args, **kwargs):
        if self.pk is None:
            # Get the current highest index and add 1
            max_index = Product.objects.aggregate(models.Max('index'))['index__max']
            self.index = (max_index or 0) + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        current_index = self.index
        super().delete(*args, **kwargs)
        # Reindex remaining products
        products = Product.objects.filter(index__gt=current_index).order_by('index')
        for product in products:
            product.index -= 1
            product.save()

    
class Offer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,null=True, blank=True)
    discount_percentage = models.IntegerField(null=True, blank=True)
    discount_name = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
   

    def __str__(self):
        return f"Offer {self.discount_percentage}%"
    
class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount_percentage = models.IntegerField(null=True, blank=True)    
    discount_name = models.CharField(max_length=255,null=True,blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - ({self.discount_percentage}%)"

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True, null = True)

    def __str__(self):
        return f"{self.product.name}: {self.rating} stars by {self.user.username}"
    

class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='CartItem')
  


    def __str__(self):
        return f"Cart of {self.user.username}"
    
    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_date = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) in cart of {self.cart.user.username}"

class Wishlist(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='WishlistItem')

    def __str__(self):         
        return f"Wishlist of {self.user.username}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} in wishlist of {self.wishlist.user.username}"

    


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    username = models.CharField(max_length=150,null=True)  # Add username field
    password = models.CharField(max_length=128,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        self.expires_at = timezone.now() + timedelta(seconds=60)  # OTP valid for 5 minutes
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP for {self.email}"
    

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    users = models.ManyToManyField(CustomUser, through='CouponUsage')

    def __str__(self):
        return self.code
    
class CouponUsage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)