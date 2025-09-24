from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # POS Interface
    path('', views.pos_index, name='pos_index'),
    path('api/product-lookup/', views.product_lookup_api, name='product_lookup_api'),
    path('api/checkout/', views.checkout_api, name='checkout_api'),
    
    # Invoice views
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/print/', views.invoice_print, name='invoice_print'),
    path('invoice/<int:invoice_id>/print/<str:template>/', views.invoice_print, name='invoice_print_template'),
    
    # Sales management
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customer/add/', views.customer_add, name='customer_add'),
    path('customer/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
]