from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from .models import ShopProfile


def profile_detail(request):
    """View shop profile"""
    shop_profile = ShopProfile.get_shop_profile()
    context = {
        'shop_profile': shop_profile,
        'page_title': 'Shop Profile'
    }
    return render(request, 'profiles/profile_detail.html', context)


def profile_edit(request):
    """Edit shop profile"""
    shop_profile = ShopProfile.get_shop_profile()
    
    if request.method == 'POST':
        shop_profile.shop_name = request.POST.get('shop_name', '').strip()
        shop_profile.gstin = request.POST.get('gstin', '').strip() or None
        shop_profile.phone = request.POST.get('phone', '').strip() or None
        shop_profile.address = request.POST.get('address', '').strip() or None
        shop_profile.default_gst_rate = request.POST.get('default_gst_rate', '5.00')
        shop_profile.invoice_prefix = request.POST.get('invoice_prefix', 'INV').strip()
        
        shop_profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profiles:profile_detail')
    
    context = {
        'shop_profile': shop_profile,
        'page_title': 'Edit Shop Profile'
    }
    return render(request, 'profiles/profile_edit.html', context)


def set_inventory_password(request):
    """Set inventory access password"""
    shop_profile = ShopProfile.get_shop_profile()
    
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 4:
            messages.error(request, 'Password must be at least 4 characters long')
        else:
            shop_profile.set_inventory_password(password)
            shop_profile.save()
            messages.success(request, 'Inventory password set successfully')
            return redirect('profiles:profile_detail')
    
    context = {
        'shop_profile': shop_profile,
        'page_title': 'Set Inventory Password'
    }
    return render(request, 'profiles/set_password.html', context)