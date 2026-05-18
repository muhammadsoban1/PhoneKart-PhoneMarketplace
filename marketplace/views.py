from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import CustomUser
from seller.models import addProduct, ShopRegistration, ShopDetail, BookingOrder
from customAdmin.models import Brand, Model, Specification
from django.db.models import Q

# Create your views here.

# Main Marketplace Page
def main_marketplace(request, user_id=None):
    if user_id:
        user = get_object_or_404(CustomUser, pk=user_id)
    else:
        user = request.user

    query = request.GET.get('q', '').strip()
    products = addProduct.objects.filter(isActive=True)

    if query:
        products = products.filter(model__icontains=query)

    condition = request.GET.get('condition')
    city = request.GET.get('city')
    color = request.GET.get('color')
    exchange = request.GET.get('exchange')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if condition:
        products = products.filter(condition=condition)
    if city:
        products = products.filter(fk_ShopID__city__iexact=city)
    if color:
        products = products.filter(Q(colors=color) | Q(color2=color))
    if exchange:
        exchange_value = exchange.lower() == 'true'
        products = products.filter(exchange=exchange_value)
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    context = {
        'products': products,
        'user': user,
    }
    return render(request, 'main_marketplace.html', context)

# Search Suggestions
def search_suggestions(request):
    query = request.GET.get('term', '')
    suggestions = []
    if query:
        suggestions = list(
            addProduct.objects.filter(model__icontains=query)
            .values_list('model', flat=True)
            .distinct()
        )
    return JsonResponse(suggestions, safe=False)

# Logout
def custom_logout(request):
    logout(request)
    return redirect('/')

# Product Description Page (FIXED ERROR HERE)
def product_description_page(request, product_id):
    user = request.user
    product = get_object_or_404(addProduct, productID=product_id)
    product_images = product.images.all()

    related_models = addProduct.objects.filter(
        brand1=product.brand1, isActive=True
    ).exclude(productID=product_id)[:4]

    # CHECK: Sirf login user ke liye booking check karein
    existing_booking_order = None
    if user.is_authenticated:
        existing_booking_order = BookingOrder.objects.filter(
            user=user,
            product=product,
            status='Active'
        ).first()

    model_instance = Model.objects.filter(name=product.model).first()
    specifications = Specification.objects.filter(model=model_instance)

    product_table_desc = [
        {'label': 'Brand', 'value': product.brand1},
        {'label': 'Model', 'value': product.model},
        {'label': 'Condition', 'value': product.condition},
        {'label': 'Colors', 'value': product.colors},
        {'label': 'Price', 'value': f'Rs. {product.price}'},
        {'label': 'Stock', 'value': product.stock},
        {'label': 'Exchange Available', 'value': 'Yes' if product.exchange else 'No'},
    ]

    context = {
        'user': user,
        'product': product,
        'product_images': product_images,
        'related_models': related_models,
        'productTableDesc': product_table_desc,
        'existing_booking_order': existing_booking_order,
        'specifications': specifications,
    }
    return render(request, 'productDescriptionPage.html', context)

@csrf_exempt
def get_seller_info(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            shop_id = data.get("shop_id")
            shop = ShopRegistration.objects.get(shopID=shop_id)
            return JsonResponse({
                "success": True,
                "phone": shop.user.phone,
                "address": shop.city,
            })
        except (ShopRegistration.DoesNotExist, json.JSONDecodeError):
            return JsonResponse({"success": False, "message": "Shop not found."})
    return JsonResponse({"success": False, "message": "Invalid request method."})

# Signup
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'signup.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return render(request, 'signup.html')

        user = CustomUser(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
        )
        user.set_password(password)
        user.save()
        return redirect('marketplace:signin')
    return render(request, 'signup.html')

# Signin
def signin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        if user:
            login(request, user)
            return redirect('marketplace:main_marketplace', user_id=user.id)
        else:
            return render(request, 'signin.html', {"error": "Invalid email or password."})
    return render(request, 'signin.html')

def cart(request):
    return render(request, 'cart.html')

def store_page(request, store_id):
    shop = get_object_or_404(ShopRegistration, pk=store_id)
    products = addProduct.objects.filter(fk_ShopID=shop, isActive=True)
    shopdetail = ShopDetail.objects.filter(fk_ShopID=shop).first()

    context = {
        'shop': shop,
        'products': products,
        'shopdetail': shopdetail,
    }
    return render(request, 'shopkeeperStore.html', context)

def bookingform(request):
    return render(request, 'bookingform.html')

def aboutUs(request):
    return render(request, 'aboutUs.html')

def privacyPolicy(request): 
    return render(request, 'privacyPolicy.html')