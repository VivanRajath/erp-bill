from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Customer, Invoice, InvoiceItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'gstin', 'created_at')
    search_fields = ('name', 'phone', 'email', 'gstin')
    ordering = ('name',)
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Address & GST', {
            'fields': ('address', 'gstin')
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'description', 'quantity', 'unit_price_incl', 'tax_rate', 'total_amount')
    readonly_fields = ('total_amount',)
    
    def total_amount(self, obj):
        if obj.pk:
            return f"₹{obj.total_amount}"
        return "-"
    total_amount.short_description = "Total Amount"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'get_customer_name', 'total_incl', 'payment_status', 'balance_due', 'created_at')
    list_filter = ('payment_status', 'date', 'created_at')
    search_fields = ('number', 'customer__name', 'customer_name', 'notes')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('number', 'date', 'customer', 'customer_name')
        }),
        ('Totals', {
            'fields': ('total_incl', 'total_base', 'total_tax'),
            'classes': ('collapse',)
        }),
        ('Payment', {
            'fields': ('payment_status', 'amount_paid')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        })
    )
    
    readonly_fields = ('total_incl', 'total_base', 'total_tax', 'created_at', 'updated_at')
    inlines = [InvoiceItemInline]
    
    def get_customer_name(self, obj):
        return obj.get_customer_display_name()
    get_customer_name.short_description = 'Customer'
    
    def balance_due(self, obj):
        balance = obj.balance_due
        if balance > 0:
            return format_html('<span style="color: red;">₹{}</span>', balance)
        else:
            return format_html('<span style="color: green;">₹{}</span>', balance)
    balance_due.short_description = 'Balance Due'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        
        # Generate invoice number if not set
        if not obj.number:
            obj.number = obj.generate_invoice_number()
        
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Recalculate totals after saving items
        form.instance.calculate_totals()


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price_incl', 'tax_rate', 'total_amount')
    list_filter = ('tax_rate',)
    search_fields = ('description', 'invoice__number', 'product__name')
    ordering = ('-invoice__created_at', 'pk')
    
    fieldsets = (
        ('Item Details', {
            'fields': ('invoice', 'product', 'description')
        }),
        ('Pricing', {
            'fields': ('quantity', 'unit_price_incl', 'tax_rate')
        }),
        ('Calculated Fields', {
            'fields': ('unit_price_base', 'unit_tax_amount', 'base_amount', 'tax_amount', 'total_amount'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('unit_price_base', 'unit_tax_amount', 'base_amount', 'tax_amount', 'total_amount')
    
    def unit_price_base(self, obj):
        if obj.pk:
            return f"₹{obj.unit_price_base}"
        return "-"
    unit_price_base.short_description = "Unit Price (Base)"
    
    def unit_tax_amount(self, obj):
        if obj.pk:
            return f"₹{obj.unit_tax_amount}"
        return "-"
    unit_tax_amount.short_description = "Unit Tax Amount"
    
    def base_amount(self, obj):
        if obj.pk:
            return f"₹{obj.base_amount}"
        return "-"
    base_amount.short_description = "Line Base Amount"
    
    def tax_amount(self, obj):
        if obj.pk:
            return f"₹{obj.tax_amount}"
        return "-"
    tax_amount.short_description = "Line Tax Amount"
    
    def total_amount(self, obj):
        if obj.pk:
            return f"₹{obj.total_amount}"
        return "-"
    total_amount.short_description = "Line Total"