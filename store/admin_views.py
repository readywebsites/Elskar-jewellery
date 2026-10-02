import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.urls import reverse

from .models import (
    Category, Product, ProductImage, Order, OrderItem,
    ContactInquiry, NewsletterSubscriber
)


def is_staff_or_superuser(user):
    """Access guard helper."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def admin_dashboard_view(request):
    """
    Luxury Atelier Admin Dashboard — Executive Command Center.
    Presents comprehensive analytics, product management, order processing,
    category control, and client inquiry resolution.
    """
    # Inline Admin Sign-In Handler if user is not yet logged in as staff
    if request.method == 'POST' and 'admin_login_submit' in request.POST:
        u_val = request.POST.get('username', '').strip()
        p_val = request.POST.get('password', '')
        user = None
        if '@' in u_val:
            u_obj = User.objects.filter(email__iexact=u_val).first()
            if u_obj:
                user = authenticate(request, username=u_obj.username, password=p_val)
        else:
            user = authenticate(request, username=u_val, password=p_val)

        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f"Namaste, {user.first_name or user.username}. Executive atelier access granted.")
            return redirect('admin_dashboard')
        elif user:
            messages.error(request, "Access restricted. Staff or administrator credentials required.")
        else:
            messages.error(request, "Invalid administrator credentials. Please verify your username and password.")

    # Access Gate
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        context = {
            'is_authorized': False,
        }
        return render(request, 'admin-dashboard.html', context)

    context = get_admin_dashboard_context(request)
    return render(request, 'admin-dashboard.html', context)


def get_admin_dashboard_context(request):
    """Calculate and collect all operational & financial metrics, records, and choices."""
    from .models import Cart, CartItem, Wishlist, Address

    # 1. CORE FINANCIAL & OPERATIONAL KPIS
    gross_revenue = Order.objects.exclude(status='cancelled').aggregate(
        total_rev=Sum('total')
    )['total_rev'] or Decimal('0.00')

    total_orders = Order.objects.count()
    orders_pending = Order.objects.filter(status='pending').count()
    orders_confirmed = Order.objects.filter(status='confirmed').count()
    orders_processing = Order.objects.filter(status='processing').count()
    orders_shipped = Order.objects.filter(status='shipped').count()
    orders_out_for_delivery = Order.objects.filter(status='out_for_delivery').count()
    orders_delivered = Order.objects.filter(status='delivered').count()
    orders_cancelled = Order.objects.filter(status='cancelled').count()
    active_orders_count = orders_pending + orders_confirmed + orders_processing + orders_shipped + orders_out_for_delivery

    total_products = Product.objects.count()
    active_products = Product.objects.filter(active=True).count()
    low_stock_products = Product.objects.filter(stock__lte=5, active=True).count()
    out_of_stock_products = Product.objects.filter(stock=0, active=True).count()

    total_customers = User.objects.filter(is_staff=False).count()
    total_subscribers = NewsletterSubscriber.objects.count()
    unresolved_inquiries = ContactInquiry.objects.filter(is_resolved=False).count()

    # 2. FILTERING & SEARCHING (TAB-SPECIFIC)
    # Orders Tab Query
    orders_qs = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')
    order_status_filter = request.GET.get('order_status', '').strip()
    order_search_query = request.GET.get('order_q', '').strip()

    if order_status_filter:
        orders_qs = orders_qs.filter(status=order_status_filter)
    if order_search_query:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=order_search_query) |
            Q(full_name__icontains=order_search_query) |
            Q(email__icontains=order_search_query) |
            Q(phone__icontains=order_search_query)
        )
    orders_list = orders_qs[:100]

    # Products Tab Query
    products_qs = Product.objects.select_related('category', 'subcategory').prefetch_related('gallery_images').order_by('-created_at')
    prod_cat_filter = request.GET.get('prod_cat', '').strip()
    prod_search_query = request.GET.get('prod_q', '').strip()
    prod_stock_filter = request.GET.get('prod_stock', '').strip()

    if prod_cat_filter:
        products_qs = products_qs.filter(Q(category__slug=prod_cat_filter) | Q(subcategory__slug=prod_cat_filter))
    if prod_search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=prod_search_query) |
            Q(sku__icontains=prod_search_query) |
            Q(material__icontains=prod_search_query)
        )
    prod_status_filter = request.GET.get('prod_status', '').strip()
    if prod_status_filter == 'active':
        products_qs = products_qs.filter(active=True)
    elif prod_status_filter == 'hidden':
        products_qs = products_qs.filter(active=False)

    if prod_stock_filter == 'low':
        products_qs = products_qs.filter(stock__lte=5)
    elif prod_stock_filter == 'out':
        products_qs = products_qs.filter(stock=0)

    products_list = products_qs[:120]

    # Categories Tab Query
    categories = Category.objects.select_related('parent').annotate(product_count=Count('products')).order_by('order', 'name')
    main_categories = Category.objects.filter(parent__isnull=True).order_by('order', 'name')
    subcategories = Category.objects.filter(parent__isnull=False).select_related('parent').order_by('parent__name', 'order', 'name')

    # Customers Tab Query
    customers_list = User.objects.filter(is_staff=False).annotate(orders_count=Count('orders')).order_by('-date_joined')[:100]

    # Active Carts Tab Query
    carts_list = Cart.objects.select_related('user').prefetch_related('items__product').order_by('-updated_at')[:60]

    # Wishlists Tab Query
    wishlists_list = Wishlist.objects.select_related('user', 'product').order_by('-created_at')[:60]

    # Inquiries Tab Query
    inquiries_list = ContactInquiry.objects.order_by('is_resolved', '-created_at')[:80]

    # Newsletter Subscribers Tab Query
    subscribers_list = NewsletterSubscriber.objects.order_by('-subscribed_at')[:100]

    # Overview Watchlists
    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:8]
    low_stock_watchlist = Product.objects.filter(stock__lte=5, active=True).order_by('stock')[:8]
    recent_inquiries = ContactInquiry.objects.filter(is_resolved=False).order_by('-created_at')[:5]

    # Active Tab Selection
    active_tab = request.GET.get('tab', 'overview').strip()

    return {
        'is_authorized': True,
        'active_tab': active_tab,

        # Metrics
        'gross_revenue': gross_revenue,
        'total_orders': total_orders,
        'active_orders_count': active_orders_count,
        'orders_pending': orders_pending,
        'orders_confirmed': orders_confirmed,
        'orders_processing': orders_processing,
        'orders_shipped': orders_shipped,
        'orders_out_for_delivery': orders_out_for_delivery,
        'orders_delivered': orders_delivered,
        'orders_cancelled': orders_cancelled,

        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,

        'total_customers': total_customers,
        'total_subscribers': total_subscribers,
        'unresolved_inquiries': unresolved_inquiries,

        # Data Lists
        'orders': orders_list,
        'products': products_list,
        'categories': categories,
        'main_categories': main_categories,
        'subcategories': subcategories,
        'customers': customers_list,
        'carts': carts_list,
        'wishlists': wishlists_list,
        'inquiries': inquiries_list,
        'subscribers': subscribers_list,

        'recent_orders': recent_orders,
        'low_stock_watchlist': low_stock_watchlist,
        'recent_inquiries': recent_inquiries,

        # Choices & Filters
        'order_status_choices': Order.STATUS_CHOICES,
        'current_order_status': order_status_filter,
        'current_order_search': order_search_query,
        'current_prod_cat': prod_cat_filter,
        'current_prod_search': prod_search_query,
        'current_prod_stock': prod_stock_filter,
        'current_prod_status': prod_status_filter,
    }



# ==============================================================================
# ORDER MANAGEMENT CONTROLLERS
# ==============================================================================

@require_POST
def admin_order_update_status(request, order_id):
    """Update order delivery status and payment status with audit notification."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '').strip()
    new_payment_status = request.POST.get('payment_status', '').strip()
    notes = request.POST.get('notes', '').strip()

    valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
    if new_status and new_status in valid_statuses:
        order.status = new_status

    if new_payment_status:
        order.payment_status = new_payment_status

    if notes:
        order.notes = notes

    order.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'message': f"Order #{order.order_number} status updated to {order.get_status_display()}.",
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_status': order.payment_status,
        })

    messages.success(request, f"Order #{order.order_number} consignment updated to {order.get_status_display()}.")
    return redirect(f"{reverse('admin_dashboard')}?tab=orders")


def admin_order_detail_api(request, order_id):
    """Retrieve full consignment receipt details, line items, and patron address."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id)

    items_data = []
    for item in order.items.all():
        img_url = item.product.image.url if (item.product and item.product.image) else ''
        sku = item.product.sku if item.product else '—'
        items_data.append({
            'name': item.name,
            'sku': sku,
            'price': float(item.price),
            'quantity': item.quantity,
            'total_price': float(item.total_price),
            'image': img_url,
        })

    data = {
        'success': True,
        'order': {
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.full_name,
            'email': order.email,
            'phone': order.phone,
            'address': order.address,
            'city': order.city,
            'state': order.state,
            'postal_code': order.postal_code,
            'subtotal': float(order.subtotal),
            'shipping_fee': float(order.shipping_fee),
            'total': float(order.total),
            'payment_method': order.payment_method,
            'payment_status': order.payment_status,
            'status': order.status,
            'status_display': order.get_status_display(),
            'notes': order.notes,
            'created_at': order.created_at.strftime('%d %b %Y, %I:%M %p'),
            'items': items_data,
        }
    }
    return JsonResponse(data)


# ==============================================================================
# PRODUCT CATALOG MANAGEMENT CONTROLLERS
# ==============================================================================

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

def is_valid_image_file(file_obj):
    """Validate that uploaded file is an allowed image type."""
    import os
    if not file_obj:
        return True
    ext = os.path.splitext(file_obj.name)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


@require_POST
def admin_product_create(request):
    """Create a new jewellery creation in the catalog."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    name = request.POST.get('name', '').strip()
    price = request.POST.get('price', '').strip()
    sale_price = request.POST.get('sale_price', '').strip() or None
    category_id = request.POST.get('category_id')
    subcategory_id = request.POST.get('subcategory_id')
    stock = request.POST.get('stock', '10').strip()
    sku = request.POST.get('sku', '').strip()
    material = request.POST.get('material', '').strip() or '22K Gold Plated Brass, Cubic Zirconia'
    care_instructions = request.POST.get('care_instructions', '').strip()
    description = request.POST.get('description', '').strip()

    featured = request.POST.get('featured') in ('1', 'true', 'on', True)
    best_seller = request.POST.get('best_seller') in ('1', 'true', 'on', True)
    new_arrival = request.POST.get('new_arrival') in ('1', 'true', 'on', True)
    active = request.POST.get('active', '1') in ('1', 'true', 'on', True)

    if not name or not price:
        messages.error(request, "Product name and price are mandatory fields.")
        return redirect(f"{reverse('admin_dashboard')}?tab=products")

    try:
        price_val = Decimal(price)
        sale_val = Decimal(sale_price) if sale_price else None
        stock_val = max(0, int(stock))
    except Exception as e:
        messages.error(request, f"Invalid pricing or stock numbers: {e}")
        return redirect(f"{reverse('admin_dashboard')}?tab=products")

    category = None
    if category_id:
        category = Category.objects.filter(id=category_id).first()

    subcategory = None
    if subcategory_id:
        subcategory = Category.objects.filter(id=subcategory_id).first()
        if subcategory and not category and subcategory.parent:
            category = subcategory.parent

    # Main Image Validation
    if 'image' in request.FILES:
        main_img = request.FILES['image']
        if not is_valid_image_file(main_img):
            messages.error(request, f"Invalid image file '{main_img.name}'. Only .jpg, .jpeg, .png, and .webp images are accepted.")
            return redirect(f"{reverse('admin_dashboard')}?tab=products")

    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    if sku and Product.objects.filter(sku__iexact=sku).exists():
        messages.error(request, f"SKU '{sku}' is already assigned to another creation.")
        return redirect(f"{reverse('admin_dashboard')}?tab=products")

    product = Product(
        name=name,
        slug=slug,
        category=category,
        subcategory=subcategory,
        price=price_val,
        sale_price=sale_val,
        stock=stock_val,
        material=material,
        description=description,
        featured=featured,
        best_seller=best_seller,
        new_arrival=new_arrival,
        active=active,
    )
    if sku:
        product.sku = sku
    if care_instructions:
        product.care_instructions = care_instructions

    if 'image' in request.FILES:
        product.image = request.FILES['image']

    product.save()

    # Gallery Images Upload
    for g_img in request.FILES.getlist('gallery_images'):
        if is_valid_image_file(g_img):
            ProductImage.objects.create(product=product, image=g_img)
        else:
            messages.warning(request, f"Skipped '{g_img.name}': only .jpg, .jpeg, .png, and .webp files are supported.")

    messages.success(request, f"Product '{product.name}' published successfully to the storefront.")
    return redirect(f"{reverse('admin_dashboard')}?tab=products")


@require_http_methods(['GET', 'POST'])
def admin_product_edit(request, product_id):
    """Retrieve product details (GET) or update product fields (POST)."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'GET':
        gallery_list = [
            {'id': gi.id, 'url': gi.image.url}
            for gi in product.gallery_images.all()
        ]
        data = {
            'id': product.id,
            'name': product.name,
            'category_id': product.category_id,
            'subcategory_id': product.subcategory_id,
            'sku': product.sku,
            'price': float(product.price),
            'sale_price': float(product.sale_price) if product.sale_price else '',
            'stock': product.stock,
            'material': product.material,
            'care_instructions': product.care_instructions,
            'description': product.description,
            'featured': product.featured,
            'best_seller': product.best_seller,
            'new_arrival': product.new_arrival,
            'active': product.active,
            'image_url': product.image.url if product.image else '',
            'gallery': gallery_list,
        }
        return JsonResponse({'success': True, 'product': data})

    # POST Update
    name = request.POST.get('name', '').strip()
    price = request.POST.get('price', '').strip()
    sale_price = request.POST.get('sale_price', '').strip()
    category_id = request.POST.get('category_id')
    subcategory_id = request.POST.get('subcategory_id')
    stock = request.POST.get('stock', '').strip()
    sku = request.POST.get('sku', '').strip()
    material = request.POST.get('material', '').strip()
    care_instructions = request.POST.get('care_instructions', '').strip()
    description = request.POST.get('description', '').strip()

    if name:
        if name != product.name:
            product.name = name
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(id=product.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            product.slug = slug

    if price:
        try:
            product.price = Decimal(price)
        except Exception:
            pass
    if sale_price:
        try:
            product.sale_price = Decimal(sale_price)
        except Exception:
            pass
    else:
        product.sale_price = None

    if stock:
        try:
            product.stock = max(0, int(stock))
        except Exception:
            pass

    if sku and sku != product.sku:
        if Product.objects.filter(sku__iexact=sku).exclude(id=product.id).exists():
            messages.error(request, f"SKU '{sku}' is already assigned to another creation.")
            return redirect(f"{reverse('admin_dashboard')}?tab=products")
        product.sku = sku
    elif not sku and not product.sku:
        product.sku = None

    if material:
        product.material = material
    if care_instructions:
        product.care_instructions = care_instructions
    if description:
        product.description = description

    if category_id is not None:
        if category_id == '' or category_id == '0':
            product.category = None
        else:
            product.category = Category.objects.filter(id=category_id).first()

    if subcategory_id is not None:
        if subcategory_id == '' or subcategory_id == '0':
            product.subcategory = None
        else:
            subcat = Category.objects.filter(id=subcategory_id).first()
            product.subcategory = subcat
            if subcat and not product.category and subcat.parent:
                product.category = subcat.parent

    product.featured = request.POST.get('featured') in ('1', 'true', 'on', True)
    product.best_seller = request.POST.get('best_seller') in ('1', 'true', 'on', True)
    product.new_arrival = request.POST.get('new_arrival') in ('1', 'true', 'on', True)
    product.active = request.POST.get('active') in ('1', 'true', 'on', True)

    # Main Image Replace / Remove
    if request.POST.get('remove_main_image') == '1':
        product.image = None
    elif 'image' in request.FILES:
        main_img = request.FILES['image']
        if not is_valid_image_file(main_img):
            messages.error(request, f"Invalid main image format '{main_img.name}'. Allowed: .jpg, .jpeg, .png, .webp.")
            return redirect(f"{reverse('admin_dashboard')}?tab=products")
        product.image = main_img

    product.save()

    # Additional Gallery Images
    for g_img in request.FILES.getlist('gallery_images'):
        if is_valid_image_file(g_img):
            ProductImage.objects.create(product=product, image=g_img)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f"Product '{product.name}' updated successfully."})

    messages.success(request, f"Product '{product.name}' updated successfully.")
    return redirect(f"{reverse('admin_dashboard')}?tab=products")


@require_POST
def admin_gallery_image_delete(request, image_id):
    """Delete a specific gallery image belonging to a product."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    img = get_object_or_404(ProductImage, id=image_id)
    img.delete()
    return JsonResponse({'success': True, 'message': 'Gallery image removed.'})


@require_POST
def admin_product_toggle_active(request, product_id):
    """Toggle a product's active status (deactivate/activate)."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    product = get_object_or_404(Product, id=product_id)
    product.active = not product.active
    product.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'active': product.active,
            'message': f"Product '{product.name}' is now {'Active' if product.active else 'Deactivated'}."
        })

    messages.success(request, f"Product '{product.name}' is now {'Active' if product.active else 'Deactivated'}.")
    return redirect(f"{reverse('admin_dashboard')}?tab=products")


@require_POST
def admin_product_delete(request, product_id):
    """Safely archive or delete a creation from the catalog."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    product = get_object_or_404(Product, id=product_id)
    name = product.name
    product.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f"Product '{name}' deleted successfully."})

    messages.success(request, f"Product '{name}' deleted from catalog.")
    return redirect(f"{reverse('admin_dashboard')}?tab=products")


@require_POST
def admin_product_quick_stock(request, product_id):
    """Quick AJAX stock refill and active status toggling."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)


    product = get_object_or_404(Product, id=product_id)

    delta = request.POST.get('delta')
    exact = request.POST.get('exact')
    toggle_active = request.POST.get('toggle_active')

    if delta:
        try:
            product.stock = max(0, product.stock + int(delta))
        except Exception:
            pass

    if exact is not None:
        try:
            product.stock = max(0, int(exact))
        except Exception:
            pass

    if toggle_active == '1':
        product.active = not product.active

    product.save()

    return JsonResponse({
        'success': True,
        'stock': product.stock,
        'active': product.active,
        'is_in_stock': product.is_in_stock,
    })


# ==============================================================================
# CATEGORY MANAGEMENT CONTROLLERS
# ==============================================================================

@require_POST
def admin_category_create(request):
    """Create a new collection silhouette/category."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    parent_id = request.POST.get('parent_id')
    menu_group = request.POST.get('menu_group', '').strip() or 'SHOP BY STYLE'
    active = request.POST.get('active', '1') in ('1', 'true', 'on', True)

    if not name:
        messages.error(request, "Category name is mandatory.")
        return redirect(f"{reverse('admin_dashboard')}?tab=categories")

    parent = None
    if parent_id and parent_id not in ('', '0'):
        parent = Category.objects.filter(id=parent_id).first()

    if Category.objects.filter(name__iexact=name, parent=parent).exists():
        messages.error(request, f"Category '{name}' already exists.")
        return redirect(f"{reverse('admin_dashboard')}?tab=categories")

    cat = Category(
        name=name,
        description=description,
        active=active,
        parent=parent,
        menu_group=menu_group
    )
    if 'image' in request.FILES:
        cat.image = request.FILES['image']
    cat.save()

    messages.success(request, f"Collection silhouette '{cat.name}' created.")
    return redirect(f"{reverse('admin_dashboard')}?tab=categories")


@require_POST
def admin_category_delete(request, category_id):
    """Remove a category safely."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    cat = get_object_or_404(Category, id=category_id)
    name = cat.name
    cat.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f"Category '{name}' deleted."})

    messages.success(request, f"Collection '{name}' removed.")
    return redirect(f"{reverse('admin_dashboard')}?tab=categories")


# ==============================================================================
# CLIENT CONCIERGE & INQUIRIES
# ==============================================================================

@require_POST
def admin_inquiry_toggle(request, inquiry_id):
    """Toggle resolved/unresolved state of a concierge client inquiry."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    inquiry = get_object_or_404(ContactInquiry, id=inquiry_id)
    inquiry.is_resolved = not inquiry.is_resolved
    inquiry.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_resolved': inquiry.is_resolved,
            'message': f"Inquiry from {inquiry.name} marked as {'Resolved' if inquiry.is_resolved else 'Pending'}."
        })

    messages.success(request, f"Inquiry marked as {'Resolved' if inquiry.is_resolved else 'Pending'}.")
    return redirect(f"{reverse('admin_dashboard')}?tab=inquiries")


# ==============================================================================
# REST / JSON API ENDPOINTS (FULL HEADLESS & RETRO-COMPATIBILITY)
# ==============================================================================

@csrf_exempt
def api_admin_login(request):
    """POST /api/admin/login — Administrator authentication endpoint."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = None
    if '@' in username:
        u_obj = User.objects.filter(email__iexact=username).first()
        if u_obj:
            user = authenticate(request, username=u_obj.username, password=password)
    else:
        user = authenticate(request, username=username, password=password)

    if user and (user.is_staff or user.is_superuser):
        login(request, user)
        return JsonResponse({'ok': True, 'message': 'Authenticated'})
    elif user:
        return JsonResponse({'ok': False, 'message': 'Staff or administrator privileges required'}, status=403)
    return JsonResponse({'ok': False, 'message': 'Invalid username or password'}, status=401)


@csrf_exempt
def api_admin_logout(request):
    """POST /api/admin/logout — Log out administrator session."""
    logout(request)
    return JsonResponse({'ok': True})


def api_admin_status(request):
    """GET /api/admin/status — Check current administrative auth state."""
    logged_in = is_staff_or_superuser(request.user)
    return JsonResponse({
        'logged_in': logged_in,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else False,
        'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
    })


def api_admin_dashboard(request):
    """GET /api/dashboard — Comprehensive metrics payload."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    sales = Order.objects.exclude(status='cancelled').aggregate(s=Sum('total'))['s'] or 0
    return JsonResponse({
        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'customers': User.objects.filter(is_staff=False).count(),
        'sales': float(sales),
        'low_stock': Product.objects.filter(stock__lte=5, active=True).count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'inquiries': ContactInquiry.objects.filter(is_resolved=False).count(),
    })


@csrf_exempt
def api_categories(request):
    """GET /api/categories (list) or POST /api/categories (create)."""
    if request.method == 'GET':
        cats = Category.objects.filter(active=True).values('id', 'name', 'slug')
        return JsonResponse(list(cats), safe=False)

    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'message': 'Category name required'}, status=400)

    cat, created = Category.objects.get_or_create(name=name)
    return JsonResponse({'ok': True, 'id': cat.id, 'name': cat.name})


@csrf_exempt
def api_category_detail(request, category_id):
    """DELETE /api/categories/<id> — Delete category."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    cat = get_object_or_404(Category, id=category_id)
    if request.method == 'DELETE':
        cat.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_admin_orders(request):
    """GET /api/orders — List latest orders for admin."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    orders = Order.objects.order_by('-created_at')[:100]
    out = []
    for o in orders:
        out.append({
            'id': o.id,
            'order_no': o.order_number,
            'customer_name': o.full_name,
            'email': o.email,
            'phone': o.phone,
            'total': float(o.total),
            'status': o.get_status_display(),
            'status_raw': o.status,
            'payment_status': o.payment_status,
            'created_at': o.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse(out, safe=False)


@csrf_exempt
def api_admin_order_status(request, order_id):
    """PUT/POST /api/orders/<id>/status — Update order status."""
    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    order = get_object_or_404(Order, id=order_id)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    new_status = data.get('status', '').strip()
    valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
    if new_status in valid_statuses:
        order.status = new_status
        order.save()
        return JsonResponse({'ok': True, 'status': order.status, 'status_display': order.get_status_display()})
    return JsonResponse({'ok': False, 'message': 'Invalid status code'}, status=400)


@csrf_exempt
def api_product_detail(request, product_id):
    """GET /api/products/<id>, PUT/POST update, DELETE product."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'GET':
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'sku': product.sku,
            'price': float(product.price),
            'sale_price': float(product.sale_price) if product.sale_price else None,
            'stock': product.stock,
            'category': product.category.name if product.category else '',
            'category_id': product.category_id,
            'subcategory': product.subcategory.name if product.subcategory else '',
            'subcategory_id': product.subcategory_id,
            'description': product.description,
            'image': product.image.url if product.image else '',
            'featured': product.featured,
            'new_arrival': product.new_arrival,
            'active': product.active,
        })

    if not is_staff_or_superuser(request.user):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    if request.method == 'DELETE':
        product.delete()
        return JsonResponse({'ok': True})

    if request.method in ('PUT', 'POST'):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        if 'name' in data:
            product.name = data['name']
        if 'price' in data and data['price']:
            product.price = Decimal(str(data['price']))
        if 'sale_price' in data:
            product.sale_price = Decimal(str(data['sale_price'])) if data['sale_price'] else None
        if 'stock' in data and data['stock'] is not None:
            product.stock = int(data['stock'])
        if 'description' in data:
            product.description = data['description']
        if 'category' in data and data['category']:
            cat = Category.objects.filter(name__iexact=data['category']).first()
            if cat:
                product.category = cat
        if 'category_id' in data:
            product.category = Category.objects.filter(id=data['category_id']).first() if data['category_id'] else None
        if 'subcategory_id' in data:
            product.subcategory = Category.objects.filter(id=data['subcategory_id']).first() if data['subcategory_id'] else None
            if product.subcategory and not product.category and product.subcategory.parent:
                product.category = product.subcategory.parent
        if 'featured' in data:
            product.featured = bool(data['featured'])
        if 'new_arrival' in data:
            product.new_arrival = bool(data['new_arrival'])
        if 'active' in data:
            product.active = bool(data['active'])

        product.save()
        return JsonResponse({'ok': True, 'id': product.id})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
