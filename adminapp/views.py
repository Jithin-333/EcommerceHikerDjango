from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from adminapp.models import CustomUser
from django. views. decorators. cache import never_cache,cache_control,cache_page
from .forms import CouponForm
import traceback
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

#product

from django.contrib import messages
from .models import Product, Category, Variant, Image,Offer,VariantOption, Coupon, CategoryOffer
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image as PILImage
import io
from django.db.models import Q

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views import View

from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta,datetime
from products.models import Order,OrderItem, ReturnedProduct, OrderItem


from django.views import View
from django.http import HttpResponse
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper, Avg,Case, When, Value
from django.db.models.functions import Coalesce, TruncDate,Greatest
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils.decorators import method_decorator
from decimal import Decimal
import csv
import json
from django.utils.dateparse import parse_date

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from django.core.exceptions import ValidationError

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger





@never_cache
def admin_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect(admin_user_view)
        return render(request, 'adminlogin.html')
    return render(request, 'adminlogin.html')



def admin_login(request):
    try:
        if request.method == "POST":
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email or not password:
                error_message = "Both email and password are required."
                return render(request, 'adminlogin.html', {'error_message': error_message})
            

            User = get_user_model()


            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect(admin_login_view)
                else:
                    error_message = "You do not have permission to access the admin site."
                    return render(request, 'adminlogin.html', {'error_message': error_message})
        else:
            error_message = "Invalid credentials."
            return render(request, 'adminlogin.html', {'error_message': error_message})
    except:
        error_message = "Invalid email or password Try again"
        return render(request, 'adminlogin.html', {'error_message': error_message})

        
@never_cache
def admin_logout(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            logout(request)
        return redirect(admin_login_view)
    return redirect(admin_login_view)



#----------------------------------------------------------------------------#
#-------------------------CUSTOMER PAGE VIEW FUNCTIONS-----------------------#
#----------------------------------------------------------------------------#

@never_cache
def admin_user_view(request):
    if request.user.is_superuser:
        user = CustomUser.objects.all().order_by('id')
        return render(request, 'userdetails.html',{'users' : user})
    return redirect(admin_login_view)

# block button function

User = get_user_model()


def toggle_block_user(request, user_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            user = get_object_or_404(User, id=user_id)
            user.is_active = not user.is_active
            user.save()
            return redirect(admin_user_view)
        return render(request, 'adminlogin.html')
    return render(request, 'adminlogin.html')

#customer search function
@never_cache
def customer_search(request):
    if request.method == "POST":
        user_details = request.POST.get('search')
        if user_details is not None:
            user = User.objects.filter(first_name__icontains=user_details).order_by('first_name')
        else:
            user = User.objects.all()  
        return render(request,'userdetails.html',{'users':user})
    


#----------------------------------------------------------------------------#
#-------------------------PRODUCT PAGE VIEW FUNCTIONS------------------------#
#----------------------------------------------------------------------------#

def product_list(request):
    if request.user.is_superuser:
        product = Product.objects.all().order_by('id')
        categories = Category.objects.all()
        variants = Variant.objects.all()
        return render(request, 'admin_products_list.html',{'products' : product,'categories': categories, 'variants': variants})
    return redirect(admin_login_view)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def add_product(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            short_description = request.POST.get('short_description')
            description = request.POST.get('description')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            category_id = request.POST.get('category')
            variant_id = request.POST.get('variant')
            images = request.FILES.getlist('images')
            offer_type = request.POST.get('offer_type')
            discount_percentage = request.POST.get('discount_percentage')
            variant_option_id = request.POST.get('variant_option')

            

            # Validation
            if not all([name, short_description, description, price, stock, category_id, variant_id, variant_option_id]):
                return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid price or stock value'}, status=400)

            category = Category.objects.get(id=category_id)
            variant = Variant.objects.get(id=variant_id)
            variant_option = VariantOption.objects.get(id=variant_option_id)

            product = Product.objects.create(
                name=name,
                short_description=short_description,
                description=description,
                price=price,
                stock=stock,
                category=category,
                variant=variant,
                variant_option=variant_option
            )

            for image_file in request.FILES.getlist('images'):
                image = Image.objects.create(image=image_file)
                product.images.add(image)

            if discount_percentage:
                discount_percentage = int(discount_percentage)
                if product.offer_set.exists():
                    offer = product.offer_set.first()
                    offer.discount_percentage = discount_percentage
                    offer.save()
                else:
                    offer = Offer.objects.create(
                        product=product,
                        discount_percentage=discount_percentage
                    )
                    product.offer_set.add(offer)

            return JsonResponse({'status': 'success', 'message': 'Product added successfully!'})
        except Exception as e:
            print(f"Error in add_product view: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # GET request handling
    categories = Category.objects.all()
    variants = Variant.objects.all()
    variant_options = VariantOption.objects.all()
    return render(request, 'add_product.html', {
        'categories': categories,
        'variants': variants,
        'variant_options': variant_options
    })


def edit_product(request,product_id):
    if request.user.is_superuser:
        product = get_object_or_404(Product, id=product_id)
        if request.method == 'POST':
            name = request.POST.get('name')
            short_description = request.POST.get('short_description')
            description = request.POST.get('description')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            category_id = request.POST.get('category')
            variant_id = request.POST.get('variant')
            variant_option_id = request.POST.get('variant_option')
            images = request.FILES.getlist('images')
            discount_percentage = request.POST.get('discount_percentage')
          
            category = Category.objects.get(id=category_id)
            variant = Variant.objects.get(id=variant_id)
            variant_option = VariantOption.objects.get(id=variant_option_id)

           

            product.name = name
            product.short_description = short_description
            product.description = description
            product.price = price
            product.stock = stock
            product.category = category
            product.variant = variant
            product.variant_option = variant_option

            product.save()

            for image_file in images:
                image = Image(image=image_file)
                image.save()
                product.images.add(image)
            product.save()

            if discount_percentage:
                discount_percentage = int(discount_percentage)
                if product.offer_set.exists():
                    offer = product.offer_set.first()
                    offer.discount_percentage = discount_percentage
                    offer.save()
                else:
                    offer = Offer.objects.create(
                        product=product,
                        discount_percentage=discount_percentage
                    )
                    product.offer_set.add(offer)

            return redirect(product_list)

        categories = Category.objects.all()
        variants = Variant.objects.all()
        variant_options = VariantOption.objects.all()

        images = product.images.all()
        offers = Offer.objects.all()
        return render(request, 'edit_product.html', {
            'products': product,
            'categories': categories,
            'variant_options': variant_options,
            'variants': variants,
            'images': images,
            'offer': offers
        })
    return redirect('admin_login_view')




def delete_image(request, image_id):
    if request.user.is_superuser:
        image = get_object_or_404(Image, id=image_id)
        image.delete()
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

def product_toggle_block(request, product_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            product = get_object_or_404(Product, id=product_id)
            product.is_active = not product.is_active
            product.save()
            return redirect(product_list)
        return render(request, 'admin_products_list.html')
    return render(request, 'admin_products_list.html')


#=============CATEGORY=========#

def category_list(request):
    if request.user.is_superuser:
        categories = Category.objects.all().prefetch_related('categoryoffer_set').order_by('added_date')
        return render(request, 'admin_category_list.html', {'categories': categories})
    return redirect(admin_login_view)

def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category')
        discount_percentage = request.POST.get('discount_percentage')
        discount_name = request.POST.get('discount_name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        new_category = Category(name=category_name)
        new_category.save()

        if discount_percentage:
            CategoryOffer.objects.create(
                category=new_category,
                discount_percentage=discount_percentage,
                discount_name=discount_name,
                start_date=start_date,
                end_date=end_date
            )

        messages.success(request, 'Category added successfully.')
        return redirect(category_list)
    return redirect(category_list)

from django.db import transaction

def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        with transaction.atomic():
            category.name = request.POST.get('name')
            category.save()

            discount_percentage = request.POST.get('discount_percentage')
            discount_name = request.POST.get('discount_name')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            offer, created = CategoryOffer.objects.get_or_create(category=category)

            if discount_percentage:
                offer.discount_percentage = (discount_percentage)
                offer.discount_name = discount_name or None
                offer.start_date = start_date or None
                offer.end_date = end_date or None
                offer.save()
            else:
                # If no discount percentage is provided, delete the offer
                offer.delete()

        messages.success(request, 'Category updated successfully.')
        return redirect(category_list)
    return redirect(category_list)

def category_toggle_block(request, category_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            category = get_object_or_404(Category, id=category_id)
            category.is_active = not category.is_active
            category.save()
            return redirect(category_list)
        return render(request, 'admin_category_list.html')
    return render(request, 'admin_category_list.html')

@user_passes_test(lambda u: u.is_superuser)
def category_search(request):
    if request.method == 'POST':
        search_query = request.POST.get('search', '')
        
        # Perform the search
        categories = Category.objects.filter(
            Q(name__icontains=search_query)
        ).order_by('name')
        
        context = {
            'categories': categories,
            'search_query': search_query,
        }
        
        return render(request, 'admin_category_list.html', context)
    return redirect('category_list')

@staff_member_required(login_url='admin_login')
def manage_variants(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_variant':
            variant_name = request.POST.get('variant_name')
            if variant_name:
                Variant.objects.create(name=variant_name)
                messages.success(request, f'Variant "{variant_name}" added successfully.')
            else:
                messages.error(request, 'Variant name is required.')
        
        elif action == 'add_option':
            variant_id = request.POST.get('variant_id')
            option_value = request.POST.get('option_value')
            if variant_id and option_value:
                variant = Variant.objects.get(id=variant_id)
                VariantOption.objects.create(variant=variant, value=option_value)
                messages.success(request, f'Option "{option_value}" added to "{variant.name}".')
            else:
                messages.error(request, 'Both variant and option value are required.')
        
        return redirect('manage_variants')

    variants = Variant.objects.all()
    return render(request, 'manage_variants.html', {'variants': variants})




@staff_member_required(login_url='admin_login')
def admin_order_list(request):
    orders_list = Order.objects.all().order_by('-created_at')
    paginator = Paginator(orders_list, 10)  # Show 10 orders per page.
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    status_choices = OrderItem.STATUS_CHOICES
   
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(OrderItem, id=item_id)
        
        if order.can_transition_to(new_status):
            order.status = new_status
            order.save()
            if new_status == "DELIVERED":
                order.payment_status='PAID'
                order.save()
            
            messages.success(request, f'Order {order.order_number} status updated successfully to {order.status}.')
            return JsonResponse({'success': True, 'message': f'Order {order.order_number} status updated successfully to {order.get_status_display()}.'})
        else:
            error_message = f'Invalid status transition from {order.get_status_display()} to {dict(OrderItem.STATUS_CHOICES)[new_status]}.'
            messages.error(request, error_message)
            return JsonResponse({'success': False, 'error': error_message}, status=400)

    context = {
        'orders': orders,
        'status_choices': status_choices
    }
    return render(request, 'admin_ordermanagement.html', context)

@staff_member_required(login_url='admin_login')
def admin_coupon_view(request):
    coupon = Coupon.objects.all()
    forms = CouponForm()
    return render(request, "admin_coupon.html",{'coupon':coupon,'form':forms})

@staff_member_required(login_url='admin_login')
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon added successfully.')
            return redirect('coupon_view')  
        else:
            messages.error(request,'Failed to add coupon. Please check the form.')
            return redirect('coupon_view')
    return redirect('coupon_view')


@staff_member_required(login_url='admin_login')
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon updated successfully.')
            return redirect('coupon_view')
        else:
            messages.error(request, 'Failed to update coupon. Please check the form.')
    return redirect(admin_coupon_view)
    
    

def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully.')
    return redirect('coupon_view')



#============ admin dashboard sale report========= #


class SalesReportView(View):
    template_name = 'sales_report.html'
    items_per_page = 5
      # Number of orders to display per page

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        report_type = request.GET.get('report_type', 'custom')
        today = timezone.now().date()

        if report_type == 'daily':
            start_date = end_date = today
        elif report_type == 'weekly':
            start_date = today - timedelta(days=7)
            end_date = today
        elif report_type == 'monthly':
            start_date = today - timedelta(days=30)
            end_date = today
        elif report_type == 'yearly':
            start_date = today - timedelta(days=365)
            end_date = today
        else:  # custom
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Convert string dates to date objects if they exist
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # If either date is missing, default to last 30 days
            if not start_date or not end_date:
                end_date = today
                start_date = end_date - timedelta(days=30)

        report_data = self.generate_report(start_date, end_date)
        
        # Pagination
         # Pagination for detailed order items
        detailed_items_paginator = Paginator(report_data['detailed_order_items'], self.items_per_page)
        detailed_items_page = request.GET.get('detailed_page', 1)
        detailed_items_page_obj = detailed_items_paginator.get_page(detailed_items_page)
    
        report_data.update({
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'report_type': report_type,
            'detailed_items_page_obj': detailed_items_page_obj,
            'payment_methods': report_data['payment_methods'],  # Ensure this is included
            'top_products': report_data['top_products'],  # Ensure this is included
        })

        return render(request, self.template_name, report_data)

    def post(self, request):
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()


            if start_date > end_date:
                raise ValueError("Start date cannot be after end date.")
            if start_date is None or end_date is None:
                raise ValueError("enter the date properly")

            report_data = self.generate_report(start_date, end_date)
            
            # Pagination for detailed order items
            detailed_items_paginator = Paginator(report_data['detailed_order_items'], self.items_per_page)
            detailed_items_page = request.POST.get('detailed_page', 1)
            detailed_items_page_obj = detailed_items_paginator.get_page(detailed_items_page)
            
            report_data.update({
                'start_date': start_date,
                'end_date': end_date,
                'report_type': 'custom',
                'detailed_items_page_obj': detailed_items_page_obj,
            })

            if 'download' in request.POST:
                return self.download_csv_report(report_data, start_date, end_date)
            if 'download_pdf' in request.POST:
                return self.download_pdf_report(report_data)

            return render(request, self.template_name, report_data)
        except ValueError as e:
            messages.error(request, str(e))
        # Re-render the template with the error message
            return self.get(request)

    

    def generate_report(self, start_date, end_date):
        cache_key = f'sales_report_{start_date}_{end_date}'
        report_data = cache.get(cache_key)
        
        if not report_data:
            orders = Order.objects.filter(created_at__date__range=[start_date, end_date]).prefetch_related('items', 'items__product', 'user')
            
            # Calculate total sales and total discount
            order_data = orders.annotate(
                order_total=Sum(F('items__price') * F('items__quantity')),
                item_discount=Sum(
                    Case(
                        When(items__offer__gt=0, then=F('items__price') * F('items__quantity') * F('items__offer') / 100),
                        default=Value(0),
                        output_field=DecimalField()
                )
            ),
            coupon_discount=Case(
                When(coupon_code__isnull=False, then=F('order_total') - F('total_amount') - F('item_discount')),
                default=Value(0),
                output_field=DecimalField()
            ),
            max_potential_discount=Sum(
                Greatest(
                    F('items__offer'),
                    Coalesce(F('items__product__offer__discount_percentage'), 0),
                    Coalesce(F('items__product__category__categoryoffer__discount_percentage'), 0)
                ) * F('items__price') * F('items__quantity') / 100
            )
            ).aggregate(
                total_sales=Sum('total_amount'),
                total_discount=Sum('item_discount') + Sum('coupon_discount'),
                total_max_potential_discount=Sum('max_potential_discount'),
                order_count=Count('id')
            )

            total_sales = order_data['total_sales'] or 0
            total_discount = order_data['total_discount'] or 0
            total_max_potential_discount = order_data['total_max_potential_discount'] or 0
            order_count = order_data['order_count'] or 0

            # Get top 5 selling products
            top_products = OrderItem.objects.filter(order__in=orders).values('product__name').annotate(
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')[:5]

            # Get top 5 customers
            top_customers = CustomUser.objects.filter(order__in=orders).annotate(
                total_spent=Sum('order__total_amount')
            ).order_by('-total_spent')[:5]

            # Daily sales data for chart
            daily_sales = orders.annotate(date=TruncDate('created_at')).values('date').annotate(
                daily_total=Sum('total_amount'),
                daily_discount=Sum(F('items__price') * F('items__quantity') - F('total_amount')),
                order_count=Count('id')
            ).order_by('date')

            daily_sales_data = [
                {
                    'date': item['date'].strftime('%Y-%m-%d'),
                    'daily_total': float(item['daily_total']),
                    'daily_discount': float(item['daily_discount']),
                    'order_count': item['order_count']
                } for item in daily_sales
            ]

            # Payment method breakdown
            payment_methods = orders.values('payment_method').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            ).order_by('-total')

            # Average order value
            avg_order_value = total_sales / order_count if order_count > 0 else 0

            # Get top 10 selling categories
            top_categories = Category.objects.filter(product__orderitem__order__in=orders).annotate(
                total_quantity=Sum('product__orderitem__quantity')
            ).order_by('-total_quantity')[:5]
            # Prepare detailed order information
            detailed_order_items = []
            for order in orders.order_by('-created_at'):
                for item in order.items.all():
                    original_price = item.price * item.quantity
                    discount_amount = Decimal(item.offer / 100) * original_price if item.offer else 0
                    discounted_price = original_price - discount_amount

                    detailed_order_items.append({
                        'order_number': item.order_number,
                        'created_at': order.created_at,
                        'user_email': order.user.email,
                        'total_amount': order.total_amount,
                        'payment_method': order.payment_method,
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'original_price': original_price,
                        'offer_percentage': item.offer,
                        'discount_amount': discount_amount,
                        'discounted_price': discounted_price,
                        'status': item.status,
                    })


            report_data = {
                'total_sales': total_sales,
                'order_count': order_count,
                'total_discount': total_discount,
                'total_max_potential_discount': total_max_potential_discount,
                'coupon_usage': orders.exclude(coupon_code__isnull=True).count(),
                'orders': orders,
                'top_products': list(top_products),
                'top_customers': top_customers,
                'daily_sales': daily_sales_data,
                'payment_methods': list(payment_methods),
                'avg_order_value': avg_order_value,
                'top_categories': list(top_categories),
                'detailed_order_items': detailed_order_items,


            }
            
            cache.set(cache_key, report_data, 60 * 60)  # Cache for 1 hour
        
        return report_data

    def download_csv_report(self, report_data, start_date, end_date):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Date', 'Customer', 'Total Amount', 'Status', 'Payment Method', 'Items'])
        
        for order in report_data['orders']:
            items = ", ".join([f"{item.product.name} ({item.quantity})" for item in order.items.all()])
            writer.writerow([
                order.id,
                order.created_at.date(),
                order.user.email,
                order.total_amount,
                order.payment_method,
                items
            ])

        return response
    def download_pdf_report(self, report_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20, bottomMargin=20, leftMargin=20, rightMargin=20)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph("Sales Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Summary Table
        summary_data = [
            ["Total Sales", f"${report_data['total_sales']:.2f}"],
            ["Order Count", str(report_data['order_count'])],
            ["Total Discount", f"${report_data['total_discount']:.2f}"],
            ["Coupon Usage", str(report_data['coupon_usage'])],
            ["Avg Order Value", f"${report_data['avg_order_value']:.2f}"],
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # Top Products Table
        elements.append(Paragraph("Top 5 Selling Products", styles['Heading2']))
        top_products_data = [["Product", "Total Quantity"]]
        top_products_data.extend([[p['product__name'], p['total_quantity']] for p in report_data['top_products']])
        top_products_table = Table(top_products_data)
        top_products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(top_products_table)
        elements.append(Spacer(1, 12))

        # Payment Methods Table
        elements.append(Paragraph("Payment Methods", styles['Heading2']))
        payment_methods_data = [["Payment Method", "Count", "Total"]]
        payment_methods_data.extend([[pm['payment_method'], pm['count'], f"${pm['total']:.2f}"] for pm in report_data['payment_methods']])
        payment_methods_table = Table(payment_methods_data)
        payment_methods_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(payment_methods_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{report_data["start_date"]}_to_{report_data["end_date"]}.pdf"'
        response.write(buffer.getvalue())
        
        return response


from django.views.generic import ListView
from products.models import WalletTransaction


from decimal import Decimal

class LedgerBookView(ListView):
    template_name = 'ledger_book.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = []
        orders = Order.objects.all().order_by('-created_at')
        wallet_transactions = WalletTransaction.objects.all().order_by('-timestamp')

        for order in orders:
            queryset.append({
                'date': order.created_at,
                'description': f"Order #{order.id}",
                'amount': order.total_amount or Decimal('0.00'),
                'type': 'debit'
            })

        for transaction in wallet_transactions:
            queryset.append({
                'date': transaction.timestamp,
                'description': transaction.description,
                'amount': transaction.amount or Decimal('0.00'),
                'type': transaction.transaction_type.lower()
            })

        return sorted(queryset, key=lambda x: x['date'], reverse=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_debit'] = sum((item['amount'] for item in self.object_list if item['type'] == 'debit'), Decimal('0.00'))
        context['total_credit'] = sum((item['amount'] for item in self.object_list if item['type'] == 'credit'), Decimal('0.00'))
        context['balance'] = context['total_debit'] - context['total_credit']
        return context
    


@staff_member_required
def manage_returns(request):
    return_requests = ReturnedProduct.objects.all().order_by('-requested_at')
    context = {
        'return_requests': return_requests,
    }
    return render(request, 'manage_returns.html', context)

@staff_member_required
def return_action(request, return_id):
    return_request = get_object_or_404(ReturnedProduct, id=return_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            return_request.status = 'approved'
            return_request.order_item.status = 'RETURNED'
            return_request.order_item.save()
            messages.success(request, f"Return request #{return_id} has been approved.")
        elif action == 'reject':
            return_request.status = 'rejected'
            messages.success(request, f"Return request #{return_id} has been rejected.")
        return_request.save()
    return redirect('manage_returns')