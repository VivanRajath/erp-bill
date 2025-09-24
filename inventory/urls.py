from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Inventory management (password protected)
    path('', views.inventory_login, name='inventory_login'),
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('logout/', views.inventory_logout, name='inventory_logout'),
    
    # Product management
    path('products/', views.product_list, name='product_list'),
    path('product/add/', views.product_add, name='product_add'),
    path('product/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Stock management
    path('stock-movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('stock-purchase/', views.stock_purchase, name='stock_purchase'),
    
    # Barcode generation
    path('barcode/generate/<int:product_id>/', views.generate_barcode, name='generate_barcode'),
    path('barcode/labels/', views.barcode_labels, name='barcode_labels'),
    path('barcode/print-sheet/', views.print_barcode_sheet, name='print_barcode_sheet'),
]