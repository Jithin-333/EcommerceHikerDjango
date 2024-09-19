from django.shortcuts import render,redirect,get_object_or_404
from django.core.paginator import Paginator
from adminapp.models import CustomUser,OTP,Product,Offer,Cart, CartItem, Category,Coupon,CouponUsage
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password,check_password


from user.otpe_mail import generate_and_send_otp 

from products.models import Wallet,WalletTransaction


from django.contrib.auth import update_session_auth_hash
from decimal import Decimal
from django.db.models import Q

from django.http import JsonResponse

from urllib.parse import urlencode






# Create your views here.

def user_login_view(request):
    if request.user.is_authenticated:
        return redirect(home)
    return render(request,"validation/user_login.html")


def user_login(request):
    if request.user.is_authenticated:
        return redirect(home)
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validate email and password fields
        if not email or not password:
            messages.warning(request, "Email and password are required.")
            return redirect('user_login')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse(home))  # Redirect to home page after successful login
        
        
        messages.warning(request, "Invalid email or password.")
        return render(request, 'validation/user_login.html')
    return render(request, 'validation/user_login.html')



def user_signup(request):
    if request.user.is_authenticated:
        return redirect(home)
    
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            messages.warning(request, "All fields are required")
            return redirect('user_signup')
    
        if ' ' in  username:
            messages.warning(request, "username is unique and can't contain spaces")
            return redirect(user_signup)
    
        
        if CustomUser.objects.filter(username=username).exists():
            messages.warning(request, "User name is already taken!")
            return redirect(user_signup)
        
        if not (email.endswith('@gmail.com') and email[0].isalpha()):
            messages.warning(request, "Enter a valid email")
            return redirect(user_signup)
        
        if CustomUser.objects.filter(email=email).exists():
            messages.warning(request, "Email is already registered!")
            return redirect(user_signup)
        
        if len(password) < 8:
            messages.warning(request, "Password must be at least 8 characters")
            return redirect(user_signup)

        
        if password != confirm_password:
            messages.warning(request, "password not matching")
            return redirect(user_signup)
        
         # Hash the password before saving

        new_user = get_user_model().objects.create(
            username=username,
            email=email,
            phone=phone,
            password=make_password(password),
            is_active=False  # User is initially inactive
        )
        new_user.save()


        otp = generate_and_send_otp(email)
        OTP.objects.create(email=email, otp=otp )
        messages.success(request, "OTP sent to your email. Please validate.")
        return render(request, "validation/validate_otp.html", {'email': email})
    return render(request,'validation/user_signup.html')
        

from .signals import user_otp_verified

def validate_otp(request):
    if request.method == "POST":
        
        email = request.POST.get('email')
        otp = request.POST.get('otp')

        try:
            otp_record = OTP.objects.get(email=email, otp=otp)
            if otp_record.is_valid():
                # Activate user by sending the signal
                user_otp_verified.send(sender=OTP, email=email)

                otp_all=OTP.objects.all()
                otp_all.delete()
                messages.success(request, "Account created successfully. Please log in.")
                return redirect('user_login')
            else:
                messages.warning(request, "OTP has expired")
        except OTP.DoesNotExist:
            messages.warning(request, "Invalid OTP")

        return render(request, 'validation/validate_otp.html', {'email': email})



def resend_otp(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        # Generate and send a new OTP
        otp = generate_and_send_otp(email)
        
        # Update the OTP record
        OTP.objects.create(email=email, otp=otp)

        messages.success(request, "A new OTP has been sent to your email.")
        return render(request,'validation/validate_otp.html',{'email': email})

    return render(request, 'validation/validate_otp.html',{'email': email})


def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect(home)
    

def forgot_password(request):
    email = request.POST.get("email")
    try:
        if CustomUser.objects.filter(email=email).exists():
            otp=generate_and_send_otp(email)
            OTP.objects.create(email=email, otp=otp)
            return render(request, "validation/otp_forgot_validation.html",{'email': email})
    except:
        messages.warning(request,"Enter you email")
        return render(request, "validation/forgot_password_email.html")
    
    return render(request, "validation/forgot_password_email.html")

def password_otp_validate(request):
    if request.method == "POST":
        
        email = request.POST.get('email')
        otp = request.POST.get('otp')

        try:
            otp_record = OTP.objects.get(email=email, otp=otp)
            if otp_record.is_valid():
                
                otp_record.delete()
                return render(request,'validation/change_password.html',{'email':email})
            else:
                messages.warning(request, "OTP has expired")
        except OTP.DoesNotExist:
            messages.warning(request, "Invalid OTP")

        return render(request, 'validation/forgot_password_email.html', {'email': email})
    return render(request, 'validation/forgot_password_email.html')

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email") 
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password and confirm_password and password == confirm_password:
            try:
                user = CustomUser.objects.get(email=email)
                user.password=make_password(password)
                user.save()
                messages.success(request, 'password successfully changed.')
                return redirect(user_login)
            except CustomUser.DoesNotExist:
                messages.warning(request, 'User does not exist.')
        else:
            messages.warning(request, 'Passwords do not match or are empty.')
            return render(request, 'validation/change_password.html',{'email':email})



    

# ============user product and home ===========

def home(request):
    
    offers = Offer.objects.all()
    offer_products = {offer.product.id: offer.discount_percentage for offer in offers}

    products = Product.objects.filter(is_active=True).select_related('category', 'variant').prefetch_related('images')
    
    all_product = []
    for product in products:
        discount_percentage = offer_products.get(product.id, None)
        all_product.append({
            'product': product,
            'discount_percentage': discount_percentage
        })

    if request.user.is_authenticated:
        user = request.user # Fetch the authenticated user from CustomUser model

        return render(request, "home.html",{"user":user,'all_products': all_product})
    return render(request,"home.html",{'all_products': all_product})



def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    for item in similar_products:
        item.offers = item.offer_set.all()

    return render(request, 'product_detailed_view.html', {'product': product,'similar_products': similar_products})

def explore(request):
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'default')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.filter(is_active=True).select_related('category', 'variant').prefetch_related('images')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category:
        products = products.filter(category__name=category)

    # Convert queryset to list and calculate offer price
    product_list = list(products)
    for product in product_list:
        product.calculated_offer_price = product.offer_price

    # Apply price filters
    if min_price:
        product_list = [p for p in product_list if p.calculated_offer_price >= Decimal(min_price)]
    if max_price:
        product_list = [p for p in product_list if p.calculated_offer_price <= Decimal(max_price)]

    # Sorting
    if sort_by == 'price_low_to_high':
        product_list.sort(key=lambda p: p.calculated_offer_price)
    elif sort_by == 'price_high_to_low':
        product_list.sort(key=lambda p: p.calculated_offer_price, reverse=True)
    elif sort_by == 'new_arrivals':
        product_list.sort(key=lambda p: p.id, reverse=True)
    elif sort_by == 'a_to_z':
        product_list.sort(key=lambda p: p.name)
    elif sort_by == 'z_to_a':
        product_list.sort(key=lambda p: p.name, reverse=True)

    paginator = Paginator(product_list, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get all categories and price range for filters
    categories = Category.objects.all()
    price_range = {
        'min_price': min(p.calculated_offer_price for p in product_list) if product_list else None,
        'max_price': max(p.calculated_offer_price for p in product_list) if product_list else None,
    }
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    get_params_string = urlencode(get_params)

    context = {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'search_query': search_query,
        'categories': categories,
        'min_price': price_range['min_price'],
        'max_price': price_range['max_price'],
        'selected_category': category,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'get_params': get_params_string,
    }

    if request.user.is_authenticated:
        context['user'] = request.user

    return render(request, "explore.html", context)

#   #########  ==========PROFILE SECTION VIEW FUNCTIONS HERE========  #########   #
#   #########  ==========PROFILE SECTION VIEW FUNCTIONS HERE========  #########   #
#   #########  ==========PROFILE SECTION VIEW FUNCTIONS HERE========  #########   #
#   #########  ==========PROFILE SECTION VIEW FUNCTIONS HERE========  #########   #

@login_required(login_url='user_login')
def user_profile(request):
    if request.user.is_authenticated:
        user=request.user
        user_data=CustomUser.objects.get(id=user.id)
    return render(request, "profile/user_profile.html",{"user":user_data})


@never_cache
@login_required(login_url='user_login')
def edit_profile(request):
    if request.user.is_authenticated:
        user=request.user
        user=CustomUser.objects.get(id=user.id)
        if request.method == "POST":
            user.first_name=request.POST.get("firstname")
            user.last_name=request.POST.get("lastname")
            user.email=request.POST.get("email")
            user.phone=request.POST.get("phone")
            user.addressOne=request.POST.get("permanentaddress")
            user.street_address=request.POST.get("streetaddress")
            user.city=request.POST.get("city")
            user.postal_code=request.POST.get("postalcode")
            user.state=request.POST.get("state")
            user.country=request.POST.get("country")

            try:
                if any(char.isdigit() for char in user.first_name) or ' ' in user.first_name or ' ' in user.last_name or any(char.isdigit() for char in user.last_name):
                    messages.error(request,"Invalid Name, Don't enter other Charactes")
                    return render(request,"profile/edit_profile.html")
                
                if not (user.email.endswith('@gmail.com') and user.email[0].isalpha()):
                    messages.error(request,"Enter a Valid Email")
                    return render(request,"profile/edit_profile.html")
            except:
                messages.error(request,"something Happened, Sorry for the Inconvienience")
                return render(request,"profile/edit_profile.html")
            
            user.save()
            messages.success(request,"Successfully made the Changes")
            return render(request,"profile/edit_profile.html",{"user":user})
        
    return render(request,"profile/edit_profile.html",{"user":user})


@login_required(login_url='user_login')
def profile_change_password(request):
    if request.user.is_authenticated:
        user = request.user

        if request.method == "POST":
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
             
            # Validate current password
            if not check_password(current_password, user.password):
                messages.warning(request, "Current password is incorrect.")
                return redirect("edit_profile")
            
            if new_password != confirm_password:
                messages.warning(request, "New passwords do not match.")
                return redirect("edit_profile")
            
            if len(new_password) < 8:
                messages.warning(request, "Password must be at least 8 characters long.")
                return redirect("edit_profile")

            hashed_password = make_password(new_password)
            user.password = hashed_password
            user.save()

            # Update session authentication hash
            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully.")
            return redirect("edit_profile")  

        # GET request or initial rendering of the form
        return render(request, "profile/edit_profile.html")
    return render(request, "profile/edit_profile.html")


@login_required(login_url='user_login')
def wallet(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by('-timestamp')[:10]  # Get the latest 10 transactions
    return render(request, 'cart_wishlist/wallet.html', {'wallet': wallet, 'transactions': transactions})



@login_required(login_url='user_login')
def coupon_list(request):
    user = request.user
    coupons = Coupon.objects.all()
    used_coupons = CouponUsage.objects.filter(user=user).values_list('coupon_id', flat=True)

    context = {
        'coupons': coupons,
        'used_coupons': used_coupons,
    }
    return render(request, 'cart_wishlist/coupon_list.html', context)