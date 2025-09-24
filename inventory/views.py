from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction, models
from decimal import Decimal
import io

from .models import Product, StockMovement, BarcodeLabel, Collection
from profiles.models import ShopProfile


def inventory_login(request):
    """Login to inventory management"""
    if request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_dashboard')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        shop_profile = ShopProfile.get_shop_profile()
        
        if shop_profile.check_inventory_password(password):
            request.session['inventory_authenticated'] = True
            return redirect('inventory:inventory_dashboard')
        else:
            messages.error(request, 'Invalid password')
    
    context = {'page_title': 'Inventory Access'}
    return render(request, 'inventory/login.html', context)


def inventory_logout(request):
    """Logout from inventory management"""
    request.session.pop('inventory_authenticated', None)
    messages.info(request, 'Logged out from inventory management')
    return redirect('inventory:inventory_login')


def inventory_dashboard(request):
    """Inventory management dashboard"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(track_stock=True, stock_quantity__lt=5).count()
    recent_movements = StockMovement.objects.select_related('product').order_by('-timestamp')[:10]
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
        'page_title': 'Inventory Dashboard'
    }
    return render(request, 'inventory/dashboard.html', context)


def product_list(request):
    """List all products"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    products = Product.objects.all().order_by('name')
    search = request.GET.get('search', '').strip()
    
    if search:
        products = products.filter(
            models.Q(name__icontains=search) |
            models.Q(sku__icontains=search) |
            models.Q(barcode_value__icontains=search)
        )
    
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'page_title': 'Products'
    }
    return render(request, 'inventory/product_list.html', context)


def product_add(request):
    """Add new product"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        barcode_value = request.POST.get('barcode_value', '').strip() or None
        collection_name = request.POST.get('collection', '').strip()
        price_incl = request.POST.get('price_incl_tax', '').strip()
        cost_price = request.POST.get('cost_price', '').strip()
        tax_rate = request.POST.get('tax_rate', '').strip() or '5.0'
        stock_quantity = request.POST.get('stock_quantity', '').strip() or '0'

        if not name:
            messages.error(request, 'Product name is required')
        else:
            collection = None
            if collection_name:
                collection, _ = Collection.objects.get_or_create(name=collection_name)
            try:
                product = Product.objects.create(
                    name=name,
                    collection=collection,
                    barcode_value=barcode_value,
                    price_incl_tax=Decimal(price_incl or '0'),
                    tax_rate=Decimal(tax_rate),
                    cost_price=Decimal(cost_price or '0'),
                    track_stock=True,
                    stock_quantity=Decimal(stock_quantity)
                )
                messages.success(request, 'Product created')
                return redirect('inventory:product_list')
            except Exception as e:
                messages.error(request, f'Error creating product: {e}')

    collections = Collection.objects.all()
    context = {'page_title': 'Add Product', 'collections': collections}
    return render(request, 'inventory/product_form.html', context)


def product_edit(request, product_id):
    """Edit product"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.barcode_value = request.POST.get('barcode_value', '').strip() or None
        collection_name = request.POST.get('collection', '').strip()
        price_incl = request.POST.get('price_incl_tax', '').strip()
        cost_price = request.POST.get('cost_price', '').strip()
        tax_rate = request.POST.get('tax_rate', '').strip() or '5.0'
        stock_quantity = request.POST.get('stock_quantity', '').strip() or '0'

        product.price_incl_tax = Decimal(price_incl or '0')
        product.cost_price = Decimal(cost_price or '0')
        product.tax_rate = Decimal(tax_rate)
        product.stock_quantity = Decimal(stock_quantity)
        if collection_name:
            collection, _ = Collection.objects.get_or_create(name=collection_name)
            product.collection = collection
        else:
            product.collection = None
        if not product.name:
            messages.error(request, 'Product name is required')
        else:
            try:
                product.save()
                messages.success(request, 'Product updated')
                return redirect('inventory:product_list')
            except Exception as e:
                messages.error(request, f'Error updating product: {e}')

    collections = Collection.objects.all()
    context = {
        'product': product,
        'collections': collections,
        'page_title': f'Edit Product - {product.name}'
    }
    return render(request, 'inventory/product_form.html', context)


def product_delete(request, product_id):
    """Delete product"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    product = get_object_or_404(Product, id=product_id)
    context = {
        'product': product,
        'page_title': f'Delete Product - {product.name}'
    }
    return render(request, 'inventory/product_delete.html', context)


def stock_movement_list(request):
    """List stock movements"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    movements = StockMovement.objects.select_related('product').order_by('-timestamp')
    paginator = Paginator(movements, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Stock Movements'
    }
    return render(request, 'inventory/stock_movements.html', context)


def stock_adjustment(request):
    """Adjust stock levels"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    products = Product.objects.filter(track_stock=True).order_by('name')
    context = {
        'products': products,
        'page_title': 'Stock Adjustment'
    }
    return render(request, 'inventory/stock_adjustment.html', context)


def stock_purchase(request):
    """Record stock purchase"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    products = Product.objects.filter(track_stock=True).order_by('name')
    context = {
        'products': products,
        'page_title': 'Stock Purchase'
    }
    return render(request, 'inventory/stock_purchase.html', context)


def generate_barcode(request, product_id):
    """Generate barcode for product"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    product = get_object_or_404(Product, id=product_id)
    context = {
        'product': product,
        'page_title': f'Generate Barcode - {product.name}'
    }
    return render(request, 'inventory/generate_barcode.html', context)


def barcode_labels(request):
    """Barcode label printing interface"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    products = Product.objects.exclude(barcode_value__isnull=True).exclude(barcode_value='').order_by('name')
    templates = BarcodeLabel.objects.all()
    
    context = {
        'products': products,
        'templates': templates,
        'page_title': 'Barcode Labels'
    }
    return render(request, 'inventory/barcode_labels.html', context)


def print_barcode_sheet(request):
    """Print barcode sheet"""
    if not request.session.get('inventory_authenticated'):
        return redirect('inventory:inventory_login')
    
    products = Product.objects.exclude(barcode_value__isnull=True).exclude(barcode_value='').order_by('name')
    context = {
        'page_title': 'Print Barcode Sheet',
        'products': products,
    }
    return render(request, 'inventory/barcode_sheet.html', context)