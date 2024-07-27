from django.contrib import admin
from django.urls import path,include
from user import views

urlpatterns = [

    path('',views.home, name="home"),
    path('login/',views.user_login, name="user_login"),
    path('user_login_view/',views.user_login_view, name="user_login_view"),
    path('logout/',views.user_logout, name="user_logout"),
    path('signup/',views.user_signup, name="user_signup"),
    path('validate_otp/', views.validate_otp, name='validate_otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('password_otp_validate/', views.password_otp_validate, name='password_otp_validate'),
    path('reset_password/', views.reset_password, name='reset_password'),


    path('user_profile/', views.user_profile, name='user_profile'),
    path('user_profile/edit_profile/', views.edit_profile, name='edit_profile'),
    path('user_profile/edit_profile/profile_change_password/', views.profile_change_password, name='profile_change_password'),
    

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('explore/', views.explore, name='explore'),

    path('wallet/', views.wallet, name='wallet'),
    path('coupon-list/', views.coupon_list, name='coupon_list'),

  

    ]
