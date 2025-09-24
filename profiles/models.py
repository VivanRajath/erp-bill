from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class ShopProfile(models.Model):
    shop_name = models.CharField(max_length=200, default="My Shop")
    gstin = models.CharField(max_length=15, blank=True, null=True, help_text="GST Identification Number")
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    default_gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    invoice_prefix = models.CharField(max_length=10, default="INV", help_text="Prefix for invoice numbers")
    last_invoice_number = models.IntegerField(default=0, help_text="Last generated invoice number")
    inventory_password_hash = models.CharField(max_length=128, blank=True, null=True, help_text="Password for inventory access")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Shop Profile"
        verbose_name_plural = "Shop Profiles"
    
    def __str__(self):
        return self.shop_name
    
    def set_inventory_password(self, password):
        """Set encrypted password for inventory access"""
        if password:
            self.inventory_password_hash = make_password(password)
        else:
            self.inventory_password_hash = None
    
    def check_inventory_password(self, password):
        """Check if provided password matches inventory password"""
        if not self.inventory_password_hash:
            return True  # No password set, allow access
        return check_password(password, self.inventory_password_hash)
    
    @classmethod
    def get_shop_profile(cls):
        """Get or create the shop profile (singleton pattern)"""
        profile, created = cls.objects.get_or_create(pk=1)
        return profile