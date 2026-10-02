import uuid
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse

from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Wishlist, Address, Order, OrderItem, ContactInquiry, NewsletterSubscriber
)
from .context_processors import get_user_cart


# ==============================================================================
# CATALOG & STORE VIEWS
# ==============================================================================

def home(request):
    """Luxury Homepage with curated collections, dynamic products, and editorial sections."""
    curated_categories = list(
        Category.objects.filter(parent__isnull=True, active=True).order_by('order', 'name')[:7]
    )
    categories = curated_categories
    new_arrivals = Product.objects.filter(active=True, new_arrival=True).select_related('category', 'subcategory')[:8]
    best_sellers = Product.objects.filter(active=True, best_seller=True).select_related('category', 'subcategory')[:8]
    featured_products = Product.objects.filter(active=True, featured=True).select_related('category', 'subcategory')[:4]
    bridal_category = Category.objects.filter(slug='bridal-collection', parent__isnull=True).first()
    bridal_products = (
        Product.objects.filter(active=True)
        .filter(Q(category=bridal_category) | Q(subcategory__parent=bridal_category))
        .select_related('category', 'subcategory')[:4]
        if bridal_category else []
    )

    context = {
        'curated_categories': curated_categories,
        'categories': categories,
        'new_arrivals': new_arrivals,
        'best_sellers': best_sellers,
        'featured_products': featured_products,
        'bridal_products': bridal_products,
    }
    return render(request, 'index.html', context)


def shop(request):
    """Comprehensive Shop Page with dynamic filtering, sorting, search, and pagination."""
    queryset = Product.objects.filter(active=True).select_related('category', 'subcategory')
    main_categories = Category.objects.filter(parent__isnull=True, active=True).prefetch_related('subcategories').order_by('order', 'name')

    # Category & Subcategory Filter
    cat_slug = request.GET.get('category', '').strip()
    sub_slug = request.GET.get('subcategory', '').strip()
    current_category = None
    current_subcategory = None

    if cat_slug:
        slug_aliases = {
            'bridal': 'bridal-collection',
            'sets': 'jewellery-sets',
            'jewellery-set': 'jewellery-sets',
        }
        lookup_slug = slug_aliases.get(cat_slug, cat_slug)
        found_cat = Category.objects.filter(slug=lookup_slug, active=True).first()
        if found_cat:
            if found_cat.parent:
                current_subcategory = found_cat
                current_category = found_cat.parent
                queryset = queryset.filter(Q(subcategory=found_cat) | Q(category=found_cat))
            else:
                current_category = found_cat
                queryset = queryset.filter(Q(category=found_cat) | Q(subcategory__parent=found_cat))

    if sub_slug:
        found_sub = Category.objects.filter(slug=sub_slug, active=True).first()
        if found_sub:
            current_subcategory = found_sub
            if not current_category:
                current_category = found_sub.parent
            queryset = queryset.filter(subcategory=found_sub)

    # Search Filter
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(material__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        )

    # Flag Filters
    if request.GET.get('new') == '1':
        queryset = queryset.filter(new_arrival=True)
    if request.GET.get('best') == '1':
        queryset = queryset.filter(best_seller=True)
    if request.GET.get('featured') == '1':
        queryset = queryset.filter(featured=True)
    if request.GET.get('sale') == '1':
        queryset = queryset.filter(sale_price__isnull=False)

    # Availability filter
    in_stock = request.GET.get('in_stock', '').strip()
    if in_stock == '1':
        queryset = queryset.filter(stock__gt=0)

    # Price Range Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            queryset = queryset.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'best_selling':
        queryset = queryset.order_by('-best_seller', '-rating')
    elif sort_by == 'name_asc':
        queryset = queryset.order_by('name')
    else:
        queryset = queryset.order_by('-created_at')

    total_count = queryset.count()

    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    available_subcategories = []
    if current_category:
        available_subcategories = current_category.subcategories.filter(active=True).order_by('order', 'name')

    context = {
        'products': page_obj,
        'categories': main_categories,
        'current_category': current_category,
        'current_subcategory': current_subcategory,
        'available_subcategories': available_subcategories,
        'query': query,
        'cat_slug': cat_slug,
        'sub_slug': sub_slug,
        'in_stock': in_stock,
        'sort_by': sort_by,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'total_count': total_count,
    }
    return render(request, 'shop-grid.html', context)


def category_view(request, category_slug, subcategory_slug=None):
    """
    Dedicated Luxury Category & Subcategory Landing Experience.
    Displays editorial category headers, subcategory navigation pills,
    and category-curated products.
    """
    category = get_object_or_404(Category, slug=category_slug, parent__isnull=True, active=True)
    subcategory = None
    if subcategory_slug:
        subcategory = get_object_or_404(Category, slug=subcategory_slug, parent=category, active=True)
        queryset = Product.objects.filter(active=True).filter(
            Q(subcategory=subcategory) | Q(category=subcategory)
        ).select_related('category', 'subcategory')
    else:
        queryset = Product.objects.filter(active=True).filter(
            Q(category=category) | Q(subcategory__parent=category)
        ).select_related('category', 'subcategory')

    subcategories = category.subcategories.filter(active=True).order_by('order', 'name')

    in_stock = request.GET.get('in_stock', '').strip()
    if in_stock == '1':
        queryset = queryset.filter(stock__gt=0)

    if request.GET.get('new') == '1':
        queryset = queryset.filter(new_arrival=True)
    if request.GET.get('best') == '1':
        queryset = queryset.filter(best_seller=True)
    if request.GET.get('sale') == '1':
        queryset = queryset.filter(sale_price__isnull=False)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            queryset = queryset.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'best_selling':
        queryset = queryset.order_by('-best_seller', '-rating')
    elif sort_by == 'name_asc':
        queryset = queryset.order_by('name')
    else:
        queryset = queryset.order_by('-created_at')

    total_count = queryset.count()
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'subcategory': subcategory,
        'subcategories': subcategories,
        'products': page_obj,
        'total_count': total_count,
        'sort_by': sort_by,
        'in_stock': in_stock,
        'min_price': min_price or '',
        'max_price': max_price or '',
    }
    return render(request, 'category.html', context)


def product_detail(request, slug):
    """Luxury Product Detail Page with image gallery, specs, availability, and related items."""
    product = get_object_or_404(
        Product.objects.select_related('category', 'subcategory'),
        slug=slug,
        active=True
    )
    related_products = Product.objects.filter(
        active=True
    ).filter(
        Q(category=product.category) | Q(subcategory=product.subcategory)
    ).exclude(id=product.id)[:4]

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    else:
        in_wishlist = product.id in request.session.get('wishlist_ids', [])

    context = {
        'product': product,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'product-details.html', context)


def search_view(request):
    """Dedicated search endpoint that routes directly to the shop view with query."""
    q = request.GET.get('q', '').strip()
    if q:
        return redirect(f"{reverse('shop')}?q={q}")
    return redirect('shop')


# ==============================================================================
# CART MANAGEMENT (DJANGO DATABASE & SESSION BACKED)
# ==============================================================================

def cart_detail(request):
    """Display the user's shopping bag."""
    cart = get_user_cart(request)
    cart_items = cart.items.select_related('product').all()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'free_shipping_remaining': max(Decimal('0.00'), Decimal('999.00') - cart.subtotal),
    }
    return render(request, 'cart.html', context)


def cart_add(request, product_id):
    """Add a product to the cart with stock validation and AJAX/HTTP support."""
    product = get_object_or_404(Product, id=product_id, active=True)
    quantity = int(request.POST.get('quantity', 1)) if request.method == 'POST' else int(request.GET.get('quantity', 1))
    quantity = max(1, quantity)

    if product.stock < quantity:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': False, 'message': f'Only {product.stock} items in stock.'})
        messages.error(request, f"Sorry, only {product.stock} pieces available in stock.")
        return redirect('product_detail', slug=product.slug)

    cart = get_user_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        if product.stock < (cart_item.quantity + quantity):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
                return JsonResponse({'success': False, 'message': f'Cannot add more than {product.stock} in stock.'})
            messages.warning(request, f"You already have {cart_item.quantity} in bag. Cannot exceed stock of {product.stock}.")
            return redirect('cart')
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'message': f'Added {product.name} to your bag.',
            'cart_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'total': str(cart.total)
        })

    messages.success(request, f"Added '{product.name}' to your shopping bag.")
    return redirect('cart')


@require_POST
def cart_update(request, item_id):
    """Update item quantity or increment/decrement."""
    cart = get_user_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get('action')
    new_qty = request.POST.get('quantity')

    if action == 'increase':
        if cart_item.product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, f"Maximum available stock is {cart_item.product.stock}.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif new_qty:
        try:
            qty = int(new_qty)
            if qty <= 0:
                cart_item.delete()
            elif qty <= cart_item.product.stock:
                cart_item.quantity = qty
                cart_item.save()
            else:
                cart_item.quantity = cart_item.product.stock
                cart_item.save()
                messages.warning(request, f"Adjusted to available stock of {cart_item.product.stock}.")
        except ValueError:
            pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        item_exists = CartItem.objects.filter(id=item_id).first()
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'item_quantity': item_exists.quantity if item_exists else 0,
            'item_subtotal': str(item_exists.subtotal) if item_exists else '0.00',
            'subtotal': str(cart.subtotal),
            'shipping': str(cart.shipping_fee),
            'total': str(cart.total),
        })

    return redirect('cart')


def cart_remove(request, item_id):
    """Remove item from cart."""
    cart = get_user_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    prod_name = cart_item.product.name
    cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Removed {prod_name} from your bag.",
            'cart_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'total': str(cart.total),
        })

    messages.info(request, f"Removed '{prod_name}' from your bag.")
    return redirect('cart')


# ==============================================================================
# WISHLIST MANAGEMENT (DATABASE BACKED)
# ==============================================================================

def wishlist_detail(request):
    """Display user's saved wishlist."""
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        products = [item.product for item in wishlist_items]
    else:
        wishlist_ids = request.session.get('wishlist_ids', [])
        products = Product.objects.filter(id__in=wishlist_ids, active=True)

    context = {
        'products': products,
    }
    return render(request, 'wishlist.html', context)


def wishlist_toggle(request, product_id):
    """Toggle adding or removing an item from wishlist."""
    product = get_object_or_404(Product, id=product_id, active=True)
    added = False

    if request.user.is_authenticated:
        item = Wishlist.objects.filter(user=request.user, product=product).first()
        if item:
            item.delete()
            added = False
            msg = f"Removed '{product.name}' from your wishlist."
        else:
            Wishlist.objects.create(user=request.user, product=product)
            added = True
            msg = f"Added '{product.name}' to your wishlist."
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        wishlist_ids = request.session.get('wishlist_ids', [])
        if product.id in wishlist_ids:
            wishlist_ids.remove(product.id)
            added = False
            msg = f"Removed '{product.name}' from your wishlist."
        else:
            wishlist_ids.append(product.id)
            added = True
            msg = f"Saved '{product.name}' to your wishlist."
        request.session['wishlist_ids'] = wishlist_ids
        request.session.modified = True
        wishlist_count = len(wishlist_ids)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'added': added,
            'action': 'added' if added else 'removed',
            'message': msg,
            'wishlist_count': wishlist_count
        })

    messages.info(request, msg)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'wishlist')


def wishlist_move_to_cart(request, product_id):
    """Move an item from wishlist into the cart."""
    product = get_object_or_404(Product, id=product_id, active=True)
    cart = get_user_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Remove from wishlist
    if request.user.is_authenticated:
        Wishlist.objects.filter(user=request.user, product=product).delete()
    else:
        wishlist_ids = request.session.get('wishlist_ids', [])
        if product.id in wishlist_ids:
            wishlist_ids.remove(product.id)
            request.session['wishlist_ids'] = wishlist_ids
            request.session.modified = True

    messages.success(request, f"Moved '{product.name}' to your shopping bag.")
    return redirect('cart')


# ==============================================================================
# CHECKOUT & ORDERS
# ==============================================================================

def checkout_view(request):
    """Luxury Checkout page with order summary, address selection, and placement."""
    cart = get_user_cart(request)
    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        messages.warning(request, "Your shopping bag is empty. Add some jewellery before checking out.")
        return redirect('shop')

    addresses = []
    default_address = None
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
        default_address = addresses.filter(is_default=True).first() or addresses.first()

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        payment_method = request.POST.get('payment_method', 'Cash on Delivery')
        notes = request.POST.get('notes', '').strip()

        # If user picked a saved address
        saved_addr_id = request.POST.get('saved_address_id')
        if saved_addr_id and request.user.is_authenticated:
            saved_addr = Address.objects.filter(id=saved_addr_id, user=request.user).first()
            if saved_addr:
                full_name = saved_addr.full_name
                phone = saved_addr.phone
                address_line = f"{saved_addr.address_line1}, {saved_addr.address_line2}".strip(', ')
                city = saved_addr.city
                state = saved_addr.state
                postal_code = saved_addr.postal_code

        if not (full_name and email and phone and address_line and city and postal_code):
            messages.error(request, "Please fill in all required shipping details.")
            return render(request, 'checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'addresses': addresses,
                'default_address': default_address,
            })

        # Pre-order stock verification
        out_of_stock_items = []
        for item in cart_items:
            if item.product.stock < item.quantity:
                out_of_stock_items.append(f"'{item.product.name}' (requested: {item.quantity}, available: {item.product.stock})")

        if out_of_stock_items:
            messages.error(request, f"Some creations in your shopping bag are no longer available in the requested quantity: {', '.join(out_of_stock_items)}. Please adjust your bag.")
            return redirect('cart')

        # Save address if option checked
        if request.user.is_authenticated and request.POST.get('save_address') == '1':
            Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address_line1=address_line,
                city=city,
                state=state,
                postal_code=postal_code,
                country='India',
                is_default=(not addresses.exists())
            )

        # Create Order (prepaid orders marked Pending until payment gateway callback)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address_line,
            city=city,
            state=state,
            postal_code=postal_code,
            subtotal=cart.subtotal,
            shipping_fee=cart.shipping_fee,
            total=cart.total,
            payment_method=payment_method,
            payment_status='Pending',
            status='confirmed',
            notes=notes,
        )

        # Create Order Items and adjust inventory safely
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                name=item.product.name,
                price=item.product.current_price,
                quantity=item.quantity
            )
            # Safely decrement inventory
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save()

        # Clear Cart
        cart.items.all().delete()

        messages.success(request, f"Thank you! Your order #{order.order_number} has been confirmed.")
        return redirect('order_confirmation', order_number=order.order_number)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,
    }
    return render(request, 'checkout.html', context)


def order_confirmation(request, order_number):
    """Order confirmation and receipt page with patron authorization check."""
    order = get_object_or_404(Order, order_number=order_number)

    # Authorization guard: logged-in patron cannot view another user's order confirmation
    if order.user and request.user.is_authenticated and order.user != request.user:
        messages.error(request, "You do not have authorization to view this consignment confirmation.")
        return redirect('home')

    order_items = order.items.select_related('product').all()

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'thank-you.html', context)


@login_required
def order_detail(request, order_number):
    """Order status tracking and full details page."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = order.items.select_related('product').all()

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order-detail.html', context)


# ==============================================================================
# AUTHENTICATION & USER ACCOUNTS
# ==============================================================================

def _merge_session_cart_and_wishlist(request, user, old_session_key, old_wishlist_ids):
    """
    Merges anonymous session cart and wishlist into the authenticated user's account.
    Must be called with the old_session_key captured BEFORE django.contrib.auth.login() cycles the key.
    """
    if not user or not user.is_authenticated:
        return

    # 1. Merge Cart
    user_cart, _ = Cart.objects.get_or_create(user=user)
    if old_session_key:
        old_carts = Cart.objects.filter(session_key=old_session_key, user__isnull=True)
        for old_cart in old_carts:
            for item in old_cart.items.all():
                ci, created = CartItem.objects.get_or_create(cart=user_cart, product=item.product)
                if not created:
                    ci.quantity += item.quantity
                else:
                    ci.quantity = item.quantity
                ci.save()
            old_cart.delete()

    # Also check if current session key has an unattached cart
    current_key = request.session.session_key
    if current_key and current_key != old_session_key:
        curr_session_carts = Cart.objects.filter(session_key=current_key, user__isnull=True)
        for old_cart in curr_session_carts:
            for item in old_cart.items.all():
                ci, created = CartItem.objects.get_or_create(cart=user_cart, product=item.product)
                if not created:
                    ci.quantity += item.quantity
                else:
                    ci.quantity = item.quantity
                ci.save()
            old_cart.delete()

    # 2. Merge Wishlist
    wishlist_ids = list(old_wishlist_ids or [])
    curr_wishlist_ids = request.session.get('wishlist_ids', [])
    for wid in curr_wishlist_ids:
        if wid not in wishlist_ids:
            wishlist_ids.append(wid)

    for pid in wishlist_ids:
        p = Product.objects.filter(id=pid, active=True).first()
        if p:
            Wishlist.objects.get_or_create(user=user, product=p)

    # Clear session wishlist
    request.session['wishlist_ids'] = []
    request.session.modified = True


def login_view(request):
    """Luxury Sign-in view with Django authentication."""
    if request.user.is_authenticated:
        return redirect('account_dashboard')

    next_url = request.GET.get('next', 'account_dashboard')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Check if login with email
        user = None
        if '@' in username_or_email:
            u = User.objects.filter(email__iexact=username_or_email).first()
            if u:
                user = authenticate(request, username=u.username, password=password)
        else:
            user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            old_session_key = request.session.session_key
            old_wishlist_ids = list(request.session.get('wishlist_ids', []))
            login(request, user)
            _merge_session_cart_and_wishlist(request, user, old_session_key, old_wishlist_ids)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username/email or password. Please try again.")

    return render(request, 'authentication-login.html', {'next': next_url})


def register_view(request):
    """Luxury registration view."""
    if request.user.is_authenticated:
        return redirect('account_dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username or not email or not password:
            messages.error(request, "Please complete all mandatory fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 6:
            messages.error(request, "Password should be at least 6 characters.")
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already in use. Please select another.")
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email address already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            old_session_key = request.session.session_key
            old_wishlist_ids = list(request.session.get('wishlist_ids', []))
            login(request, user)
            _merge_session_cart_and_wishlist(request, user, old_session_key, old_wishlist_ids)
            messages.success(request, f"Welcome to Azure Jewels, {user.first_name or user.username}!")
            return redirect('account_dashboard')

    return render(request, 'authentication-register.html')


def logout_view(request):
    """Log the user out and return to home page."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')


def password_reset_view(request):
    """Luxury password reset request view."""
    if request.user.is_authenticated:
        return redirect('account_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if email and '@' in email:
            messages.success(request, "If an account exists with that email address, password reset instructions have been dispatched.")
            return redirect('login')
        else:
            messages.error(request, "Please provide a valid email address.")

    return render(request, 'authentication-reset-password.html')


@login_required
def account_dashboard(request):
    """Main customer account overview."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=request.user).count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    default_address = Address.objects.filter(user=request.user, is_default=True).first()

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'wishlist_count': wishlist_count,
        'default_address': default_address,
    }
    return render(request, 'account-dashboard.html', context)


@login_required
def account_orders(request):
    """List of all customer orders."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'account-orders.html', context)


@login_required
def account_profile(request):
    """View and update profile information."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "This email is already in use by another account.")
            else:
                user.email = email
                user.save()
                messages.success(request, "Profile updated successfully.")
        else:
            user.save()
            messages.success(request, "Profile updated successfully.")
        return redirect('account_profile')

    return render(request, 'account-profile.html')


@login_required
def account_addresses(request):
    """Manage customer shipping addresses."""
    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        is_default = request.POST.get('is_default') == '1'

        if full_name and phone and address_line1 and city and postal_code:
            Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country='India',
                is_default=is_default or not addresses.exists()
            )
            messages.success(request, "New address added successfully.")
            return redirect('account_addresses')
        else:
            messages.error(request, "Please fill in all mandatory address fields.")

    context = {
        'addresses': addresses,
    }
    return render(request, 'account-saved-address.html', context)


# ==============================================================================
# INFORMATIONAL PAGES & INQUIRIES
# ==============================================================================

def about_view(request):
    """Luxury About Us & Heritage page."""
    return render(request, 'about.html')


def store_locator_view(request):
    """Luxury Store Locator & Boutiques Showcase."""
    boutiques = [
        {
            'id': 1,
            'name': 'Azure Jewels Flagship Atelier',
            'city': 'Mumbai',
            'area': 'Bandra West',
            'address': 'Level 3, The Heritage Galleria, Linking Road, Bandra West',
            'pincode': '400050',
            'state': 'Maharashtra',
            'phone': '+91 98765 43210',
            'email': 'bandra.atelier@azurejewels.com',
            'hours': 'Monday – Sunday: 10:30 AM – 8:30 PM',
            'services': ['Bespoke Bridal Salon', 'Certified Gemmologist Consultation', 'Jewellery Spa & Ultrasonic Care', 'Valet Parking'],
            'is_flagship': True,
        },
        {
            'id': 2,
            'name': 'Azure Jewels Luxury Salon',
            'city': 'New Delhi',
            'area': 'Vasant Kunj',
            'address': 'Ground Level, DLF Emporio, Nelson Mandela Marg, Vasant Kunj',
            'pincode': '110070',
            'state': 'Delhi NCR',
            'phone': '+91 98765 43211',
            'email': 'emporio.delhi@azurejewels.com',
            'hours': 'Monday – Sunday: 11:00 AM – 9:00 PM',
            'services': ['Haute Joaillerie Showcase', 'VIP Private Lounge', 'Custom Ring Sizing', 'Valet Parking'],
            'is_flagship': False,
        },
        {
            'id': 3,
            'name': 'Azure Jewels Atelier Boutique',
            'city': 'Bengaluru',
            'area': 'UB City',
            'address': 'The Collection, Level 1, UB City, 24 Vittal Mallya Road',
            'pincode': '560001',
            'state': 'Karnataka',
            'phone': '+91 98765 43212',
            'email': 'ubcity.blr@azurejewels.com',
            'hours': 'Monday – Sunday: 10:30 AM – 8:30 PM',
            'services': ['Solitaire Specialist', 'Ultrasonic Cleaning', 'Personal Stylist Session', 'Valet Parking'],
            'is_flagship': False,
        },
        {
            'id': 4,
            'name': 'Azure Jewels Royal Pavilion',
            'city': 'Hyderabad',
            'area': 'Jubilee Hills',
            'address': 'Road No. 36, Near Peddamma Temple Metro, Jubilee Hills',
            'pincode': '500033',
            'state': 'Telangana',
            'phone': '+91 98765 43213',
            'email': 'jubilee.hyd@azurejewels.com',
            'hours': 'Monday – Sunday: 11:00 AM – 8:30 PM',
            'services': ['Heritage Bridal Sets', 'Polki & Jadau Suite', 'Private Vault Appointments', 'Valet Parking'],
            'is_flagship': False,
        },
        {
            'id': 5,
            'name': 'Azure Jewels Heritage Boutique',
            'city': 'Kolkata',
            'area': 'Park Street',
            'address': 'Park Mansions, 57A Park Street, Elgin',
            'pincode': '700016',
            'state': 'West Bengal',
            'phone': '+91 98765 43214',
            'email': 'parkstreet.kol@azurejewels.com',
            'hours': 'Monday – Sunday: 10:30 AM – 8:00 PM',
            'services': ['Heritage Necklaces', 'Gemstone Certification', 'Private Consultation'],
            'is_flagship': False,
        },
        {
            'id': 6,
            'name': 'Azure Jewels Palace Atelier',
            'city': 'Jaipur',
            'area': 'C-Scheme',
            'address': 'Mirza Ismail Road, Near Statue Circle, C-Scheme',
            'pincode': '302001',
            'state': 'Rajasthan',
            'phone': '+91 98765 43215',
            'email': 'jaipur.atelier@azurejewels.com',
            'hours': 'Monday – Sunday: 10:30 AM – 8:00 PM',
            'services': ['Kundan & Meenakari Artisan Studio', 'Bridal Trousseau Planning', 'Valet Parking'],
            'is_flagship': False,
        },
    ]
    city_filter = request.GET.get('city', '').strip()
    query_filter = request.GET.get('q', '').strip()
    
    filtered_boutiques = boutiques
    if city_filter:
        filtered_boutiques = [b for b in filtered_boutiques if b['city'].lower() == city_filter.lower()]
    if query_filter:
        q_lower = query_filter.lower()
        filtered_boutiques = [
            b for b in filtered_boutiques
            if q_lower in b['name'].lower() or q_lower in b['city'].lower() or q_lower in b['area'].lower() or q_lower in b['pincode']
        ]

    cities = sorted(list(set(b['city'] for b in boutiques)))
    context = {
        'boutiques': filtered_boutiques,
        'all_boutiques': boutiques,
        'cities': cities,
        'selected_city': city_filter,
        'search_query': query_filter,
    }
    return render(request, 'store-locator.html', context)


def track_package_view(request):
    """Real-time luxury order consignment tracking."""
    order_number = request.GET.get('order_number', '').strip() or request.POST.get('order_number', '').strip()
    identifier = request.GET.get('identifier', '').strip() or request.POST.get('identifier', '').strip()

    order = None
    order_items = []
    error_message = None
    searched = False

    masked_phone = ''
    if order_number:
        searched = True
        clean_num = order_number.replace('#', '').strip()
        query = Q(order_number__iexact=clean_num)
        if identifier:
            query &= (Q(email__iexact=identifier) | Q(phone__icontains=identifier))

        found_order = Order.objects.filter(query).first()
        if not found_order and not identifier:
            found_order = Order.objects.filter(order_number__icontains=clean_num).first()

        if found_order:
            order = found_order
            order_items = order.items.select_related('product').all()
            is_owner = (request.user.is_authenticated and order.user == request.user)
            if not is_owner and order.phone:
                p = order.phone.strip()
                masked_phone = (p[:4] + " **** " + p[-3:]) if len(p) >= 7 else "***"
            else:
                masked_phone = order.phone
        else:
            error_message = f"No consignment found matching order '{order_number}'. Please verify your details or contact Atelier Concierge."

    user_orders = []
    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]

    context = {
        'order': order,
        'order_items': order_items,
        'masked_phone': masked_phone,
        'order_number': order_number,
        'identifier': identifier,
        'searched': searched,
        'error_message': error_message,
        'user_orders': user_orders,
    }
    return render(request, 'track-package.html', context)


def contact_view(request):
    """Contact page with form submission saving to ContactInquiry."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and subject and message:
            ContactInquiry.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            messages.success(request, "Thank you for contacting Azure Jewels. Our jewellery specialist will be in touch shortly.")
            return redirect('contact')
        else:
            messages.error(request, "Please complete all mandatory fields.")

    return render(request, 'contact.html')


@require_POST
def newsletter_subscribe(request):
    """Newsletter subscription endpoint."""
    email = request.POST.get('email', '').strip().lower()
    if email and '@' in email:
        obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Thank you for subscribing to Azure Jewels Private Privileges.'})
        messages.success(request, "Thank you for subscribing to Azure Jewels Private Privileges.")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please provide a valid email address.'})
        messages.error(request, "Please provide a valid email address.")

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'home')


# ==============================================================================
# BACKWARD COMPATIBILITY ENDPOINTS
# ==============================================================================

def products_api(request):
    """JSON API for products (legacy and admin compatibility)."""
    if request.method == 'POST':
        if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
            return JsonResponse({'message': 'Unauthorized'}, status=401)
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST
        name = data.get('name', '').strip()
        price = data.get('price')
        if not name or not price:
            return JsonResponse({'ok': False, 'message': 'Name and price required'}, status=400)
        cat_name = data.get('category', '')
        category = Category.objects.filter(name__iexact=cat_name).first() if cat_name else None
        p = Product.objects.create(
            name=name,
            price=Decimal(str(price)),
            sale_price=Decimal(str(data.get('sale_price'))) if data.get('sale_price') else None,
            category=category,
            stock=int(data.get('stock', 0)),
            description=data.get('description', ''),
            featured=bool(data.get('featured')),
            new_arrival=bool(data.get('new_arrival', True)),
        )
        return JsonResponse({'ok': True, 'id': p.id})

    qs = Product.objects.filter(active=True).select_related('category')
    return JsonResponse({'products': [
        {
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'sale_price': str(p.sale_price or ''),
            'stock': p.stock,
            'image': p.image.url if p.image else '',
            'category': p.category.name if p.category else ''
        } for p in qs
    ]})


# Import Admin Management Suite Controllers
from .admin_views import (
    admin_dashboard_view,
    admin_order_update_status,
    admin_order_detail_api,
    admin_product_create,
    admin_product_edit,
    admin_product_delete,
    admin_product_quick_stock,
    admin_category_create,
    admin_category_delete,
    admin_inquiry_toggle,
    admin_gallery_image_delete,
    admin_product_toggle_active,
    api_admin_login,
    api_admin_logout,
    api_admin_status,
    api_admin_dashboard,
    api_categories,
    api_category_detail,
    api_admin_orders,
    api_admin_order_status,
    api_product_detail,
)



def page_redirect(request, target_url):
    """Redirect helper for legacy html file requests."""
    return redirect(target_url)


def buy_now(request, product_id):
    """Add product to cart with requested or default quantity and immediately proceed to checkout."""
    product = get_object_or_404(Product, id=product_id, active=True)
    if not product.is_in_stock:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('product_detail', slug=product.slug)

    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1
    qty = max(1, min(qty, product.stock))

    cart = get_user_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        cart_item.quantity = qty
    else:
        cart_item.quantity = min(cart_item.quantity + qty, product.stock)
    cart_item.save()

    return redirect('checkout')


@login_required
def address_delete(request, address_id):
    """Delete a customer address."""
    addr = get_object_or_404(Address, id=address_id, user=request.user)
    addr.delete()
    messages.success(request, "Address removed successfully.")
    return redirect('account_addresses')


@login_required
def address_set_default(request, address_id):
    """Set an address as default."""
    addr = get_object_or_404(Address, id=address_id, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    addr.is_default = True
    addr.save()
    messages.success(request, "Default shipping address updated.")
    return redirect('account_addresses')


def faq_view(request):
    """Frequently Asked Questions page."""
    return render(request, 'faq.html')


def privacy_policy_view(request):
    """Privacy & Client Confidentiality Policy."""
    return render(request, 'privacy-policy.html')


def terms_view(request):
    """Terms & Conditions of Service."""
    return render(request, 'terms.html')

terms_conditions_view = terms_view


def shipping_policy_view(request):
    """Shipping, Insured Transit & Delivery Policy."""
    return render(request, 'shipping-policy.html')


def returns_view(request):
    """Returns & Refunds Policy."""
    return render(request, 'returns.html')

return_policy_view = returns_view


def handler404(request, exception=None):
    """Custom luxury 404 error view."""
    return render(request, '404.html', status=404)


def handler500(request):
    """Custom luxury 500 server error view."""
    return render(request, '500.html', status=500)

