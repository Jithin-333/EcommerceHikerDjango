from django.contrib import admin
from django.urls import path,include
from products import views

urlpatterns = [

    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('user_cart/', views.view_cart, name='user_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add_quantity/<int:product_id>/', views.add_quantity, name='add_quantity'),
    path('sub_quantity/<int:product_id>/', views.sub_quantity, name='sub_quantity'),

    path('checkout/', views.checkout, name='checkout'),
    path('get-cart-details/', views.get_cart_details, name='get_cart_details'),
    path('get-address-details/', views.get_address_details, name='get_address_details'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-details/', views.order_details, name='order_details'),
    path('generate_pdf/<int:order_id>/<int:item_id>/', views.generate_pdf_function, name='generate_pdf_function'),


    path('order-return/<int:order_id>/<int:item_id>/', views.order_return, name='order_return'),
    path('cancel-order/<int:order_id>/<int:item_id>/', views.cancel_order, name='cancel_order'),
    


    path('user_profile/manage-addresses/', views.manage_addresses, name='manage_addresses'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('set-default-address/<int:address_id>/<str:address_type>/', views.set_default_address, name='set_default_address'),


    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('razorpay-payment/', views.razorpay_payment, name='razorpay_payment'),



    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist, name = 'wishlist'),



    ]
