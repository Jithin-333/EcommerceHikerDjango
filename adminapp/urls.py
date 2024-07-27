from django.contrib import admin
from django.urls import path
from adminapp import views

urlpatterns = [

    path('administration/',views.admin_login_view, name="admin_login_view"),
    path('admin_login/',views.admin_login, name="admin_login"),
    path('admin_logout/',views.admin_logout, name="admin_logout"),
    path('admin_user_view/',views.admin_user_view, name = "admin_user_view"),
    path('toggle_block_user/<int:user_id>/',views.toggle_block_user, name='toggle_block_user'),
    path('customer_search/',views.customer_search, name='customer_search'),

    path('admin/sales-report/', views.SalesReportView.as_view(), name='admin_sales_report'),
    path('sales-report/pdf/', views.SalesReportView.as_view(template_name='sales_report_pdf.html'), name='sales_report_pdf'),
    path('sales-report/download-pdf/', views.SalesReportView().download_pdf_report, name='download_pdf_report'),
    path('admin/ledger-book/', views.LedgerBookView.as_view(), name='ledger_book'),

    path('product_list/',views.product_list, name='product_list'),
    path('add_product/',views.add_product, name='add_product'),
    path('edit_product/<int:product_id>',views.edit_product, name='edit_product'),
    path('product_toggle_block/<int:product_id>/',views.product_toggle_block, name='product_toggle_block'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),


    path('category_list/',views.category_list, name='category_list'),
    path('add_category/',views.add_category, name='add_category'),
    path('edit_category/<int:category_id>/',views.edit_category, name='edit_category'),


    path('category_toggle_block/<int:category_id>/',views.category_toggle_block, name='category_toggle_block'),
    path('categories/', views.category_search, name='category_search'),



    path('manage-variants/', views.manage_variants, name='manage_variants'),

    path('order_management/', views.admin_order_list, name='admin_order_list'),

    path('coupon-view', views.admin_coupon_view, name='coupon_view'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),

    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete-coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    path('admin/manage-returns/', views.manage_returns, name='manage_returns'),
    path('admin/return-action/<int:return_id>/', views.return_action, name='return_action'),
    ]
