from django.contrib import admin
from django.utils.html import format_html
from .models import Product, StockMovement, BarcodeLabel


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'barcode_value', 'price_incl_tax', 'tax_rate', 'stock_quantity', 'track_stock', 'created_at')
    list_filter = ('track_stock', 'tax_rate', 'created_at')
    search_fields = ('name', 'sku', 'barcode_value', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'unit')
        }),
        ('Pricing', {
            'fields': ('price_incl_tax', 'tax_rate', 'cost_price', 'hsn')
        }),
        ('Inventory', {
            'fields': ('track_stock', 'stock_quantity')
        }),
        ('Barcode', {
            'fields': ('barcode_value',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing product
            readonly.extend(['created_at', 'updated_at'])
        return readonly


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'qty_change', 'reason', 'unit_cost', 'reference', 'timestamp')
    list_filter = ('reason', 'timestamp')
    search_fields = ('product__name', 'product__sku', 'reference', 'notes')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('product', 'qty_change', 'reason', 'unit_cost')
        }),
        ('Reference & Notes', {
            'fields': ('reference', 'notes')
        })
    )
    
    readonly_fields = ('timestamp',)
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing movement - make most fields readonly
            readonly.extend(['product', 'qty_change', 'reason', 'unit_cost'])
        return readonly


@admin.register(BarcodeLabel)
class BarcodeLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'label_width_mm', 'label_height_mm', 'columns', 'rows', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('name',)
    
    fieldsets = (
        ('Label Template', {
            'fields': ('name', 'is_default')
        }),
        ('Dimensions (mm)', {
            'fields': ('label_width_mm', 'label_height_mm')
        }),
        ('Layout', {
            'fields': ('columns', 'rows')
        }),
        ('Margins (mm)', {
            'fields': ('margin_top_mm', 'margin_left_mm', 'margin_right_mm', 'margin_bottom_mm')
        })
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_default:
            # Ensure only one default template
            BarcodeLabel.objects.exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)