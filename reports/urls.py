from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Reports dashboard
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('monthly-summary/', views.monthly_summary, name='monthly_summary'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('stock-report/', views.stock_report, name='stock_report'),
    
    # Export functionality
    path('export/sales/<str:format>/', views.export_sales, name='export_sales'),
    path('export/monthly/<str:format>/', views.export_monthly, name='export_monthly'),
]