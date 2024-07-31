# your_app_name/utils/context_processors.py

from django.contrib.auth import get_user_model
from adminapp.models import Cart, Wishlist  # Adjust the import path based on your project structure

def cart_wishlist_counts(request):
    counts = {'cart_count': 0, 'wishlist_count': 0}
    if request.user.is_authenticated:
        User = get_user_model()
        try:
            cart = Cart.objects.get(user=request.user)
            counts['cart_count'] = cart.items.count()
        except Cart.DoesNotExist:
            counts['cart_count'] = 0

        try:
            wishlist = Wishlist.objects.get(user=request.user)
            counts['wishlist_count'] = wishlist.items.count()
        except Wishlist.DoesNotExist:
            counts['wishlist_count'] = 0
    return counts
