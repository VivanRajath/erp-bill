from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP

class Collection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    collection = models.ForeignKey('Collection', on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Stock Keeping Unit")
    barcode_value = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price_incl_tax = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        validators=[MinValueValidator(Decimal('1'))],
        help_text="Price including tax"
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Tax rate percentage")
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        validators=[MinValueValidator(Decimal('0'))],
        default=0,
        help_text="Cost price per unit"
    )
    track_stock = models.BooleanField(default=True, help_text="Whether to track stock for this product")
    stock_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        default=0, 
        help_text="Current stock quantity"
    )
    hsn = models.CharField(max_length=20, blank=True, null=True, help_text="HSN/SAC Code")
    unit = models.CharField(max_length=20, default="pcs", help_text="Unit of measurement")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    def __str__(self):
        return f"{self.name} ({self.sku or 'SKU'})"
    
    @property
    def base_price(self):
        """Calculate base price excluding tax"""
        tax_multiplier = 1 + (self.tax_rate / 100)
        return (self.price_incl_tax / tax_multiplier).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def tax_amount(self):
        """Calculate tax amount"""
        return self.price_incl_tax - self.base_price
    
    def can_sell(self, quantity=1):
        """Check if we can sell the specified quantity"""
        if not self.track_stock:
            return True
        return self.stock_quantity >= quantity
    
    def adjust_stock(self, quantity_change, reason="adjustment", reference=None):
        """Adjust stock quantity and create stock movement record"""
        if self.track_stock:
            self.stock_quantity += quantity_change
            self.save()
            
            StockMovement.objects.create(
                product=self,
                qty_change=quantity_change,
                reason=reason,
                unit_cost=self.cost_price if quantity_change > 0 else None,
                reference=reference
            )

    def save(self, *args, **kwargs):
        """Auto-generate SKU and barcode if not provided."""
        creating = self.pk is None
        # First save to get an ID if creating
        if creating and (self.sku is None or self.sku == '' or self.barcode_value is None or self.barcode_value == ''):
            super().save(*args, **kwargs)
            # Now we have an ID
            if not self.sku:
                # SKU from name and collection prefix + ID
                prefix_name = (self.name or 'PRD').upper().replace(' ', '')[:3]
                prefix_coll = (self.collection.name if self.collection else 'GEN').upper().replace(' ', '')[:3]
                self.sku = f"{prefix_name}{prefix_coll}{self.pk:06d}"
            if not self.barcode_value:
                # Barcode from name+collection initials + zero-padded id
                bname = (self.name or 'PRODUCT').upper().replace(' ', '')
                bcoll = (self.collection.name if self.collection else 'GEN').upper().replace(' ', '')
                self.barcode_value = f"{bname[:3]}{bcoll[:3]}{self.pk:06d}"
            # Save again with generated fields
            return super().save(update_fields=['sku', 'barcode_value'])
        else:
            # For updates or when provided
            if not self.sku and self.pk:
                prefix_name = (self.name or 'PRD').upper().replace(' ', '')[:3]
                prefix_coll = (self.collection.name if self.collection else 'GEN').upper().replace(' ', '')[:3]
                self.sku = f"{prefix_name}{prefix_coll}{self.pk:06d}"
            if not self.barcode_value and self.pk:
                bname = (self.name or 'PRODUCT').upper().replace(' ', '')
                bcoll = (self.collection.name if self.collection else 'GEN').upper().replace(' ', '')
                self.barcode_value = f"{bname[:3]}{bcoll[:3]}{self.pk:06d}"
            return super().save(*args, **kwargs)


class StockMovement(models.Model):
    MOVEMENT_REASONS = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    qty_change = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        help_text="Positive for stock in, negative for stock out"
    )
    reason = models.CharField(max_length=20, choices=MOVEMENT_REASONS, default='adjustment')
    unit_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Unit cost for purchases"
    )
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Reference like invoice number")
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
    
    def __str__(self):
        direction = "IN" if self.qty_change > 0 else "OUT"
        return f"{self.product.name} - {abs(self.qty_change)} {direction} ({self.reason})"
    
    @property
    def total_cost(self):
        """Calculate total cost for this movement"""
        if self.unit_cost and self.qty_change > 0:
            return (self.unit_cost * self.qty_change).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        return None


class BarcodeLabel(models.Model):
    """Model to store barcode label templates"""
    name = models.CharField(max_length=100)
    label_width_mm = models.FloatField(help_text="Label width in millimeters")
    label_height_mm = models.FloatField(help_text="Label height in millimeters")
    columns = models.IntegerField(default=1, help_text="Number of columns on sheet")
    rows = models.IntegerField(default=1, help_text="Number of rows on sheet")
    margin_top_mm = models.FloatField(default=5.0)
    margin_left_mm = models.FloatField(default=5.0)
    margin_right_mm = models.FloatField(default=5.0)
    margin_bottom_mm = models.FloatField(default=5.0)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Barcode Label Template"
        verbose_name_plural = "Barcode Label Templates"
    
    def __str__(self):
        return f"{self.name} ({self.label_width_mm}x{self.label_height_mm}mm)"