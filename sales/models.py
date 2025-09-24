from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP
from inventory.models import Product


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True, help_text="Customer GSTIN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
    
    def __str__(self):
        return self.name


class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    number = models.CharField(max_length=50, unique=True)
    date = models.DateField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True, help_text="Customer name for walk-in customers")
    
    # Totals
    total_incl = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total amount including tax"
    )
    total_base = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total base amount excluding tax"
    )
    total_tax = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total tax amount"
    )
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def __str__(self):
        customer_name = self.customer.name if self.customer else (self.customer_name or "Walk-in Customer")
        return f"Invoice {self.number} - {customer_name}"
    
    def get_customer_display_name(self):
        """Get customer name for display"""
        if self.customer:
            return self.customer.name
        return self.customer_name or "Walk-in Customer"
    
    def calculate_totals(self):
        """Calculate invoice totals from items"""
        items = self.items.all()
        total_base = Decimal('0.00')
        total_tax = Decimal('0.00')
        total_incl = Decimal('0.00')
        
        for item in items:
            total_base += item.base_amount
            total_tax += item.tax_amount
            total_incl += item.total_amount
        
        self.total_base = total_base
        self.total_tax = total_tax
        self.total_incl = total_incl
        self.save()
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.total_incl - self.amount_paid
    
    def generate_invoice_number(self):
        """Generate next invoice number atomically"""
        from profiles.models import ShopProfile
        with transaction.atomic():
            shop_profile = ShopProfile.get_shop_profile()
            shop_profile.last_invoice_number += 1
            shop_profile.save()
            return f"{shop_profile.invoice_prefix}{shop_profile.last_invoice_number:04d}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.CharField(max_length=300, help_text="Product description")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit_price_incl = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Unit price including tax"
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.00,
        help_text="Tax rate percentage"
    )
    
    class Meta:
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"
    
    def __str__(self):
        return f"{self.description} (Qty: {self.quantity})"
    
    @property
    def unit_price_base(self):
        """Calculate unit price excluding tax"""
        tax_multiplier = 1 + (self.tax_rate / 100)
        return (self.unit_price_incl / tax_multiplier).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def unit_tax_amount(self):
        """Calculate unit tax amount"""
        return self.unit_price_incl - self.unit_price_base
    
    @property
    def base_amount(self):
        """Calculate total base amount for this line"""
        return (self.unit_price_base * self.quantity).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def tax_amount(self):
        """Calculate total tax amount for this line"""
        return (self.unit_tax_amount * self.quantity).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def total_amount(self):
        """Calculate total amount including tax for this line"""
        return (self.unit_price_incl * self.quantity).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def save(self, *args, **kwargs):
        """Auto-populate description and handle stock adjustments"""
        if self.product and not self.description:
            self.description = self.product.name
        
        # Handle stock adjustment for sales
        is_new = self.pk is None
        old_quantity = Decimal('0')
        
        if not is_new:
            # Get old quantity for updates
            old_item = InvoiceItem.objects.get(pk=self.pk)
            old_quantity = old_item.quantity
        
        super().save(*args, **kwargs)
        
        # Adjust stock if product tracks stock
        if self.product and self.product.track_stock:
            from inventory.models import StockMovement
            
            if is_new:
                # New item - reduce stock
                self.product.adjust_stock(
                    -self.quantity, 
                    reason='sale', 
                    reference=f"Invoice {self.invoice.number}"
                )
            else:
                # Updated item - adjust for difference
                difference = old_quantity - self.quantity
                if difference != 0:
                    self.product.adjust_stock(
                        difference, 
                        reason='sale', 
                        reference=f"Invoice {self.invoice.number} (updated)"
                    )
    
    def delete(self, *args, **kwargs):
        """Restore stock when deleting invoice items"""
        if self.product and self.product.track_stock:
            self.product.adjust_stock(
                self.quantity, 
                reason='return', 
                reference=f"Invoice {self.invoice.number} (deleted item)"
            )
        super().delete(*args, **kwargs)