from django.contrib import admin
from .models import ShopProfile


@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'gstin', 'phone', 'default_gst_rate', 'invoice_prefix', 'last_invoice_number')
    fieldsets = (
        ('Basic Information', {
            'fields': ('shop_name', 'phone', 'address', 'logo')
        }),
        ('GST & Invoice Settings', {
            'fields': ('gstin', 'default_gst_rate', 'invoice_prefix', 'last_invoice_number')
        }),
        ('Security', {
            'fields': ('inventory_password_hash',),
            'description': 'Use the profile management interface to set password securely.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at', 'inventory_password_hash')
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of shop profile
        return False
    
    def has_add_permission(self, request):
        # Only allow one shop profile
        return not ShopProfile.objects.exists()