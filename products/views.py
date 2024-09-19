from django.shortcuts import render,redirect,get_object_or_404
from adminapp.models import CustomUser, OTP, Product, Offer, Cart, CartItem,Coupon, Wishlist, WishlistItem, CouponUsage
from products.models import Order,OrderItem,CheckoutAddress, WalletTransaction, Wallet, ReturnedProduct,OrderAddress

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache



from django.utils import timezone

from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import razorpay
from django.contrib.auth import get_user_model

from django.db.models import Q, Sum, F
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
import hmac
import hashlib

from decimal import Decimal

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .forms import ReturnProductForm

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet




# Create your views here.

#===============ADD TO CART VIEW FUNCTION==================#

def add_to_cart(request, product_id, quantity=1):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':

        user = request.user
        product = Product.objects.get(id=product_id)

        stock = product.stock
        if stock == 0:
                return JsonResponse({'status': 'error', 'message': "Product is Out of Stock. Try again later."})

        cart, created = Cart.objects.get_or_create(user=user)
        
        CART_LIMIT = 10
        if cart.items.count() >= CART_LIMIT:
            return JsonResponse({'status': 'error', 'message': "Your cart is full. Please remove some items or proceed to checkout."})

        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not item_created:
            return JsonResponse({'status': 'error', 'message': "Item is already in the cart."})

        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({'status': 'success', 'message': "Item added to the cart successfully."})


@login_required(login_url='user_login')
def view_cart(request):
    # Assuming you have a way to get the current user's cart items
    cart_items = CartItem.objects.filter(cart__user=request.user).order_by('added_date')
    cart_count = cart_items.count()
    context = {
        'cart_items': cart_items,
        'cart_count': cart_count
    }
    return render(request, 'cart_wishlist/user_cart.html', context)


def remove_from_cart(request,product_id):
    user=request.user
    cart = Cart.objects.get(user=user)
    cart_item = CartItem.objects.get(cart=cart, product=product_id)
    cart_item.delete()
    return redirect(view_cart)

def add_quantity(request, product_id):
    user = request.user
    cart = get_object_or_404(Cart, user=user)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    product = Product.objects.get(id = product_id)
    stock = product.stock
    if cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()
        return JsonResponse({'success': True, 'new_quantity': cart_item.quantity})
    else:
        return JsonResponse({
            'success': False, 
            'new_quantity': stock, 
            'message': 'There is no Stock left',
        })

def sub_quantity(request,product_id):
    user=request.user
    cart = Cart.objects.get(user=user)
    cart_item = CartItem.objects.get(cart=cart, product=product_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        return JsonResponse({'success': True, 'new_quantity': cart_item.quantity})
    else:
        # cart_item.delete()
        return JsonResponse({'success': True, 'new_quantity': 1, 'item_removed': True})
    



# Address management


from .models import CheckoutAddress
from .forms import CheckoutAddressForm

@login_required(login_url='user_login')
def manage_addresses(request):
    user=request.user
    user_addresses = CheckoutAddress.objects.filter(user=user).order_by('created_at')
    
    if request.method == 'POST':
        form = CheckoutAddressForm(request.POST)
        if form.is_valid():
            if user_addresses.count() >= 6:
                messages.error(request, "You can have a maximum of 6 addresses.")
            else:
                address = form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, "Address added successfully.")
                return redirect('manage_addresses')
    else:
        form = CheckoutAddressForm()

    return render(request, 'profile/addressmanage.html', {'addresses': user_addresses, 'form': form})

@login_required(login_url='user_login')
def edit_address(request, address_id):
    address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = CheckoutAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect('manage_addresses')
    else:
        form = CheckoutAddressForm(instance=address)
    return render(request, 'profile/edit_address.html', {'form': form, 'address': address})

@login_required(login_url='user_login')
def delete_address(request, address_id):
    address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect('manage_addresses')

@login_required(login_url='user_login')
def set_default_address(request, address_id, address_type):
    address = get_object_or_404(CheckoutAddress, id=address_id, user=request.user)
    address.default = not address.default
    address.save()
    messages.success(request, f"Default {address_type} address updated.")
    return redirect('manage_addresses')


#------------CHECKOUTPAGE---------##
@never_cache
@login_required(login_url='user_login')
def checkout(request):
    try:
        user=request.user
        cart = Cart.objects.get(user=request.user)
        user_addresses = CheckoutAddress.objects.filter(user = user)
        available_coupons = Coupon.objects.filter(active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now()).exclude(users=user)
        wallet, created = Wallet.objects.get_or_create(user=request.user)

        return render(request,"cart_wishlist/checkout.html",{"user_addresses":user_addresses, "available_coupons": available_coupons,'wallet':wallet})
    except:
        messages.error(request,'error')
        return render(request,'errorpage.html')
    
    
def get_cart_details(request):
    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    product_count = cart_items.count()
    quantity_count = sum(item.quantity for item in cart_items)
    subtotal = int(sum(float(item.product.offer_price) * item.quantity for item in cart_items))
    return JsonResponse({
        'product_count':product_count,
        'quantity_count': quantity_count,
        'subtotal': subtotal,
        'total': subtotal  # Initially, total is the same as subtotal
    })


def get_address_details(request):
    address_id = request.GET.get('address_id')
    address = CheckoutAddress.objects.get(id=address_id)
    return JsonResponse({
        'name': address.name,
        'apartment_address': address.apartment_address,
        'phone': address.phone,
        'phone_alternate': address.phone_alternate,
        'city': address.city,
        'zip_code': address.zip_code,
        'state': address.state,
        'country': address.country
    })


@require_POST
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code')
    now = timezone.now()
    user = request.user
    try:
        coupon = Coupon.objects.get(code=coupon_code)
        
        if not coupon.active:
            return JsonResponse({'valid': False, 'reason': 'Coupon is not active'})
        
        if coupon.valid_from > now:
            return JsonResponse({'valid': False, 'reason': 'Coupon is not yet valid'})
        
        if coupon.valid_to < now:
            return JsonResponse({'valid': False, 'reason': 'Coupon has expired'})
        
        if coupon.users.filter(id=user.id).exists():
            return JsonResponse({'valid': False, 'reason': 'Coupon already used'})

        return JsonResponse({'valid': True, 'discount': float(coupon.discount)})
    
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'reason': 'Coupon does not exist'})


def calculate_order_total(cart_items, coupon=None):
    total_amount = sum(item.quantity * Decimal(item.product.offer_price) for item in cart_items)
    if coupon:
        total_amount -= Decimal(coupon.discount)
    return max(total_amount, Decimal('0'))

@never_cache
@login_required(login_url='user_login')
@require_POST
def place_order(request):
    user = request.user
    if request.method == "POST":
        name=request.POST.get('name')
        phone=request.POST.get('phone')
        phone_alternate=request.POST.get('phone_alternate')
        apartment_address=request.POST.get('apartment-address')
        city=request.POST.get('city')
        state=request.POST.get('state')
        country=request.POST.get('country')
        method=request.POST.get('payment-method')
        zip_code=request.POST.get('zip-code')
        save_info = request.POST.get('save-info', False)

        

         # Validation
        if not all([name, phone, apartment_address, city, state, country, zip_code]):
            return JsonResponse({'status': 'error', 'message': 'All fields except alternate phone are required.'})

        if not phone.isdigit() or len(phone) < 10:
            return JsonResponse({'status': 'error', 'message': 'Invalid phone number. Please enter at least 10 digits.'})

        if phone_alternate and (not phone_alternate.isdigit() or len(phone_alternate) < 10):
            return JsonResponse({'status': 'error', 'message': 'Invalid alternate phone number. Please enter at least 10 digits or leave it blank.'})

        if len(zip_code) < 5 or not zip_code.isdigit():
            return JsonResponse({'status': 'error', 'message': 'Invalid ZIP code. Please enter at least 5 digits.'})
        if method is None:
            return JsonResponse({'status': 'error', 'message': 'please select a Payment Method'})


        
           

        try:
           
            address_id = request.POST.get('address-select')
            coupon_code = request.POST.get('coupon_code')
            payment_method = request.POST.get('payment-method')

            

            # if address_id is not None and save_info == 'on':
            #     return JsonResponse({'status': 'error', 'message': 'Already saved address!.. Remove the tick!.'})


            # Handle address
            if save_info == 'on':
                shipping_address = OrderAddress.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    phone_alternate=phone_alternate,
                    apartment_address=apartment_address,
                    city=city,
                    state=state,
                    country=country,
                    zip_code=zip_code,
                    address_type='Home'
                )
                address_save=CheckoutAddress.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    phone_alternate=phone_alternate,
                    apartment_address=apartment_address,
                    city=city,
                    state=state,
                    country=country,
                    zip_code=zip_code,
                    address_type='Home' 
                )
                address_save.save()
            else:
                shipping_address = OrderAddress.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    phone_alternate=phone_alternate,
                    apartment_address=apartment_address,
                    city=city,
                    state=state,
                    country=country,
                    zip_code=zip_code,
                    address_type='Home' 
                )

            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                return JsonResponse({'status': 'error', 'message': 'Cart is empty.'})

            # total_amount = Decimal(0)
            # for item in cart_items:
            #     total_amount += item.quantity * Decimal(item.product.offer_price)
                
            
              # Apply coupon discount
            coupon = None
            coupon_code = request.POST.get('coupon_code')
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(
                        code=coupon_code,
                        active=True,
                        valid_from__lte=timezone.now(),
                        valid_to__gte=timezone.now()
                    )
                except Coupon.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Invalid coupon code'})

            total_amount = calculate_order_total(cart_items, coupon)

            if payment_method == 'COD' and total_amount > 1000:
                return JsonResponse({'status': 'error', 'message': 'Order should be 1000 above'})
            
             # Handle coupon usage (if applicable)
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    CouponUsage.objects.create(user=user, coupon=coupon)
                except Coupon.DoesNotExist:
                    pass

                    
            # Get or create user's wallet
            wallet, created = Wallet.objects.get_or_create(user=user)

            if payment_method == 'WALLET':
                if wallet.balance >= total_amount:
                    # Create order
                    order = Order.objects.create(
                        user=user,
                        shipping_address=shipping_address,
                        payment_method=payment_method,
                        coupon_code=coupon_code,
                        total_amount=total_amount
                        
                    )

                    # Create order items
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.offer_price,
                            offer=item.product.get_discount_percentage(),
                            payment_status='PAID'
                        )
                        item.product.stock -= item.quantity
                        item.product.save()
                        

                    # Deduct amount from wallet
                    wallet.deduct_funds(total_amount)

                    # Create wallet transaction record
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=total_amount,
                        transaction_type='DEBIT',
                        description=f'Payment for order #{order.id}'
                    )

                    # Clear cart
                    cart_items.delete()

                   

                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Order placed successfully using wallet balance.',
                        'redirect': reverse('order_details')
                    })
                else:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Insufficient wallet balance.'
                    })


            if payment_method == 'UPI_PAYMENTS':
                try:
                    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
                    razorpay_order = client.order.create({
                        "amount": int(total_amount * 100),  # Amount in paise
                        "currency": "INR",
                        "receipt": f"order_rcptid_{user.id}_{timezone.now().timestamp()}",
                        "payment_capture": '0'
                    })
                    
                    temp_order = Order.objects.create(
                        user=user,
                        shipping_address=shipping_address,
                        payment_method=payment_method,
                        coupon_code=coupon_code,
                        total_amount=total_amount,
                        razorpay_order_id=razorpay_order['id'],
                    )
                    temp_order.save()
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=temp_order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.offer_price,
                            offer=item.product.get_discount_percentage()
                        )
                

                    payment_url = reverse('razorpay_payment')
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Redirecting to payment gateway',
                        'payment_url': payment_url,
                        'order': temp_order.id,
                        'razorpay_order_id': razorpay_order['id'],
                        'razorpay_api_key': settings.RAZORPAY_API_KEY,
                        'total_amount': str(total_amount)
                    })
                except:
                    temp_order.delete()
                    return JsonResponse({'status': 'error', 'message': 'Error creating Razorpay order.'})
            
            
            
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                payment_method=payment_method,
                coupon_code=coupon_code
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.offer_price,
                    offer=item.product.get_discount_percentage()
                )
                item.product.stock -= item.quantity
                item.product.save()
            order.total_amount = total_amount
            order.save()
            cart_items.delete()
            
            return JsonResponse({'status': 'success', 'message': 'Order Confirmed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@never_cache
@login_required
def razorpay_payment(request):
    order_id = request.GET.get('order')
    razorpay_order_id = request.GET.get('razorpay_order_id')
    razorpay_api_key = request.GET.get('razorpay_api_key')
    total_amount = request.GET.get('total_amount')

    return render(request, 'cart_wishlist/razorpay_payment.html', {
        'order_id': order_id,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_api_key': razorpay_api_key,
        'total_amount': total_amount
    })


@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            try:
                client.utility.verify_payment_signature(params_dict)

                temp_order = Order.objects.get(razorpay_order_id=order_id)
                item = OrderItem.objects.all()

                temp_order.payment_id = payment_id
                temp_order.save()

                # Update product stock
                order_items = OrderItem.objects.filter(order=temp_order)
                for item in order_items:
                    item.payment_status='PAID'
                    product = item.product
                    product.stock -= item.quantity
                    product.save()
                    item.save()

                Cart.objects.filter(user=temp_order.user).delete()



                return HttpResponseRedirect(reverse('order_details') + '?success=1')
            except razorpay.errors.SignatureVerificationError:

                # Payment verification failed, delete the temporary order
                Order.objects.filter(razorpay_order_id=order_id, status='PENDING').delete()
                return HttpResponseBadRequest('Signature verification failed')

        except Exception as e:
            Order.objects.filter(razorpay_order_id=order_id, status='PENDING').delete()

            return HttpResponseBadRequest(str(e))

    return HttpResponseBadRequest('Invalid request')



@login_required(login_url='user_login')
def order_details(request):
    orders_list = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders_list, 6)  # Show 10 orders per page.
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    return render(request, 'cart_wishlist/order_details.html', {'orders': orders})


@login_required(login_url='user_login')
def order_return(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    orderitem = OrderItem.objects.get(id=item_id)
    
    if request.method == 'POST':
        form = ReturnProductForm(request.POST)
        if form.is_valid():
            if (orderitem.status == 'DELIVERED' and order.payment_method == 'UPI_PAYMENTS') or (orderitem.status == 'DELIVERED' and order.payment_method == 'WALLET') or (orderitem.status == 'DELIVERED' and order.payment_method == 'COD'):

               
                returned_product = ReturnedProduct(
                    order=order,
                    order_item=orderitem,
                    user=request.user,
                    quantity=orderitem.quantity,
                    reason=form.cleaned_data['reason'],
                    description=form.cleaned_data['description']
                )
                returned_product.save()
                # Refund the amount to the wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.add_funds(orderitem.subtotal)
                
                # Create a wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=order.total_amount,
                    transaction_type='CREDIT',
                    description=f'Refund for order #{orderitem.order_number}'
                )

                # Update product stock
                
                product = orderitem.product
                product.stock += orderitem.quantity
                product.save()
            
                orderitem.status = 'RETURNED'
                orderitem.save()
                messages.success(request, 'Order has been returned successfully and the amount has been added to your wallet.')
                return redirect('wallet')
            
            else:
                messages.error(request, 'This order cannot be returned.')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ReturnProductForm()
        

    return render(request, 'cart_wishlist/return_form.html', {'form': form, 'order': orderitem})


@never_cache
@login_required(login_url='user_login')
def cancel_order(request, order_id,item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    orderitem=OrderItem.objects.get(id=item_id)
    
    if request.method == 'POST':
        if (orderitem.status in ['PENDING', 'PROCESSING'] and order.payment_method == 'UPI_PAYMENTS') or (orderitem.status in ['PENDING', 'PROCESSING'] and order.payment_method == 'WALLET'):
            # Refund the amount to the wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.add_funds(orderitem.subtotal)
            
            # Create a wallet transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=orderitem.subtotal,
                transaction_type='CREDIT',
                description=f'Refund for cancelled order #{orderitem.order_number}'
            )

            # Update product stock
            
            product = orderitem.product
            product.stock += orderitem.quantity
            product.save()
            
            orderitem.status = 'CANCELLED'
            orderitem.save()
            
            messages.success(request, f'Order #{orderitem.order_number} has been cancelled successfully and the amount has been added to your wallet.')
            return redirect('wallet')

       
        if orderitem.status in ['PENDING', 'PROCESSING']:
      
            orderitem.status = 'CANCELLED'
            orderitem.save()
    
        
            product = orderitem.product
            product.stock += orderitem.quantity
            product.save()
            
            messages.success(request, f'Order #{orderitem.order_number} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
        
        return redirect('order_details')
    
    return redirect(reverse('order_details'))

# WISHLIST PRODUCT VIEWS
@login_required(login_url='user_login')
def wishlist(request):
    wishlist_items = WishlistItem.objects.filter(wishlist__user=request.user).select_related('product')
    return render(request, 'cart_wishlist/wishlist.html', {'wishlist_items': wishlist_items})


@login_required(login_url='user_login')
def toggle_wishlist(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':        
        product_id = request.POST.get('product_id')
        product = Product.objects.get(id = product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
            WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
            in_wishlist = False
            message = "Product removed from wishlist"
        else:
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            in_wishlist = True
            message = "Product added to wishlist"
        
        return JsonResponse({'status': 'success', 'message': message, 'in_wishlist': in_wishlist})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_function(request, order_id, item_id):
    order = Order.objects.get(id=order_id)
    orderitem = OrderItem.objects.get(id=item_id)
    
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=invoice_{orderitem.order_number}.pdf'
    
    # Create the PDF object, using the response object as its "file."
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontSize = 24  # Increase font size for title

    normal_style = styles['Normal']
   # Increase font size for normal text


    # Title
    title = Paragraph("Invoice", title_style)
    elements.append(title)
    elements.append(Spacer(1, 19))

    # Order details
    order_details = [
        ["Order Id:", orderitem.order_number],
        ["Order Date:", order.created_at.strftime('%d %b %Y')],
        ["Payment Method:", order.get_payment_method_display()],
    ]
    user_details = [
        ["User:", order.user.username],
        ["Phone:", order.shipping_address.phone],
        ["Email:", order.user.email],
    ]
    shipping_address = [
        ["Shipping Address:", ""],
        ["", order.shipping_address.name],
        ["", order.shipping_address.apartment_address],
        ["", f"{order.shipping_address.city}, {order.shipping_address.state}"],
        ["", f"{order.shipping_address.zip_code}, {order.shipping_address.country}"],
    ]

    order_table = Table(order_details, hAlign='LEFT')
    user_table = Table(user_details, hAlign='LEFT')
    shipping_table = Table(shipping_address, hAlign='LEFT')

    elements.append(order_table)
    elements.append(Spacer(1, 12))
    elements.append(user_table)
    elements.append(Spacer(1, 12))
    elements.append(shipping_table)
    elements.append(Spacer(1, 24))

    # Table header and rows
    data = [
        ["Product", "Quantity", "Offer", "Price", "Subtotal"],
        [orderitem.product.name, orderitem.quantity, orderitem.offer, f"Rs.{orderitem.price}", f"Rs.{orderitem.subtotal}"],
        ["", "", "Total", f"Rs.{orderitem.subtotal}"],
    ]

    table = Table(data, colWidths=[3 * inch, inch, inch, inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 24))

    # Footer
    footer = Paragraph("Thank you for your purchase!", normal_style)
    footer_note = Paragraph("If you have any questions about this invoice, please contact us at support@example.com.", normal_style)

    elements.append(footer)
    elements.append(Spacer(1, 12))
    elements.append(footer_note)

    # Build the PDF
    doc.build(elements)
    
    return response
