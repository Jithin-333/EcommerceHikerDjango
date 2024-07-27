
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Product, Image, Variant, Review,Category,OTP,Cart,CartItem,Wishlist,WishlistItem,Offer,VariantOption,Coupon,CouponUsage, CategoryOffer



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'first_name', 'last_name', 'email', 'phone', 'addressOne', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('username','email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'addressOne',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'phone', 'addressOne', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username','email',)
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Category)
admin.site.register(VariantOption)

admin.site.register(Product)
admin.site.register(Variant)
admin.site.register(Image)
admin.site.register(Review)
admin.site.register(OTP)
from django.contrib import admin

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 1

class WishlistAdmin(admin.ModelAdmin):
    inlines = [WishlistItemInline]

admin.site.register(Cart, CartAdmin)
admin.site.register(Wishlist, WishlistAdmin)

admin.site.register(Offer)

admin.site.register(Coupon)
admin.site.register(CouponUsage)
admin.site.register(CategoryOffer)




