from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db import models
from decimal import Decimal
import json

from .models import Invoice, InvoiceItem, Customer
from inventory.models import Product
from profiles.models import ShopProfile


def pos_index(request):
    """Main POS interface"""
    shop_profile = ShopProfile.get_shop_profile()
    context = {
        'shop_profile': shop_profile,
        'page_title': 'Point of Sale'
    }
    return render(request, 'sales/pos_index.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def product_lookup_api(request):
    """API to lookup product by barcode or search"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)
    
    try:
        # Try to find by barcode first
        product = Product.objects.get(barcode_value=query)
    except Product.DoesNotExist:
        # Try to find by name or SKU
        products = Product.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(sku__icontains=query)
        )[:10]
        
        if products.count() == 1:
            product = products.first()
        elif products.count() > 1:
            # Multiple matches - return list for selection
            results = []
            for p in products:
                results.append({
                    'id': p.id,
                    'name': p.name,
                    'sku': p.sku,
                    'barcode': p.barcode_value,
                    'price': float(p.price_incl_tax),
                    'stock': float(p.stock_quantity) if p.track_stock else None,
                    'can_sell': p.can_sell(1)
                })
            return JsonResponse({'multiple': True, 'products': results})
        else:
            return JsonResponse({'error': 'Product not found'}, status=404)
    
    # Single product found
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'barcode': product.barcode_value,
        'price': float(product.price_incl_tax),
        'tax_rate': float(product.tax_rate),
        'unit': product.unit,
        'stock': float(product.stock_quantity) if product.track_stock else None,
        'can_sell': product.can_sell(1),
        'track_stock': product.track_stock
    })


@csrf_exempt
@require_http_methods(["POST"])
def checkout_api(request):
    """API to process checkout and create invoice"""
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        customer_name = data.get('customer_name', '').strip()
        
        if not items:
            return JsonResponse({'error': 'No items in cart'}, status=400)
        
        with transaction.atomic():
            # Create invoice
            invoice = Invoice.objects.create(
                customer_name=customer_name if customer_name else None
            )
            invoice.number = invoice.generate_invoice_number()
            invoice.save()
            
            # Create invoice items
            for item_data in items:
                product_id = item_data.get('product_id')
                product = None
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                        # Check stock availability
                        qty = Decimal(str(item_data['quantity']))
                        if product.track_stock and not product.can_sell(qty):
                            return JsonResponse({
                                'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'
                            }, status=400)
                    except Product.DoesNotExist:
                        pass
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    description=item_data['description'],
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price_incl=Decimal(str(item_data['unit_price'])),
                    tax_rate=Decimal(str(item_data.get('tax_rate', 5.0)))
                )
            
            # Calculate totals
            invoice.calculate_totals()
            
        return JsonResponse({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.number,
            'total': float(invoice.total_incl)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def invoice_detail(request, invoice_id):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    context = {
        'invoice': invoice,
        'page_title': f'Invoice {invoice.number}'
    }
    return render(request, 'sales/invoice_detail.html', context)


def invoice_print(request, invoice_id, template='a4'):
    """Print invoice in specified format"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    shop_profile = ShopProfile.get_shop_profile()
    
    templates = {
        'a4': 'sales/invoice_print_a4.html',
        'a5': 'sales/invoice_print_a5.html',
        'thermal': 'sales/invoice_print_thermal.html'
    }
    
    template_name = templates.get(template, templates['a4'])
    
    context = {
        'invoice': invoice,
        'shop_profile': shop_profile,
        'print_template': template
    }
    return render(request, template_name, context)


def invoice_list(request):
    """List all invoices"""
    invoices = Invoice.objects.all().order_by('-created_at')
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Invoices'
    }
    return render(request, 'sales/invoice_list.html', context)


def customer_list(request):
    """List all customers"""
    customers = Customer.objects.all().order_by('name')
    context = {
        'customers': customers,
        'page_title': 'Customers'
    }
    return render(request, 'sales/customer_list.html', context)


def customer_add(request):
    """Add new customer"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        gstin = request.POST.get('gstin', '').strip()
        
        if not name:
            messages.error(request, 'Customer name is required')
            return render(request, 'sales/customer_form.html', {'page_title': 'Add Customer'})
        
        Customer.objects.create(
            name=name,
            phone=phone if phone else None,
            email=email if email else None,
            address=address if address else None,
            gstin=gstin if gstin else None
        )
        
        messages.success(request, 'Customer added successfully')
        return redirect('sales:customer_list')
    
    context = {'page_title': 'Add Customer'}
    return render(request, 'sales/customer_form.html', context)


def customer_edit(request, customer_id):
    """Edit customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name', '').strip()
        customer.phone = request.POST.get('phone', '').strip() or None
        customer.email = request.POST.get('email', '').strip() or None
        customer.address = request.POST.get('address', '').strip() or None
        customer.gstin = request.POST.get('gstin', '').strip() or None
        
        if not customer.name:
            messages.error(request, 'Customer name is required')
        else:
            customer.save()
            messages.success(request, 'Customer updated successfully')
            return redirect('sales:customer_list')
    
    context = {
        'customer': customer,
        'page_title': f'Edit Customer - {customer.name}'
    }
    return render(request, 'sales/customer_form.html', context)