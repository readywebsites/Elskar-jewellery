from collections import OrderedDict
from .models import Category, Cart, CartItem, Wishlist

def get_user_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
            if session_cart and session_cart != cart:
                for item in session_cart.items.all():
                    ci, created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                    if not created:
                        ci.quantity += item.quantity
                    else:
                        ci.quantity = item.quantity
                    ci.save()
                session_cart.delete()
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user__isnull=True)
        return cart

def store_context(request):
    cart_count = 0
    wishlist_count = 0
    
    try:
        cart = get_user_cart(request)
        cart_count = cart.total_items
    except Exception:
        cart_count = 0

    try:
        if request.user.is_authenticated:
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
        else:
            wishlist_ids = request.session.get('wishlist_ids', [])
            wishlist_count = len(wishlist_ids)
    except Exception:
        wishlist_count = 0

    main_cats = list(
        Category.objects.filter(parent__isnull=True, active=True)
        .prefetch_related('subcategories')
        .order_by('order', 'name')
    )

    for cat in main_cats:
        subs = list(cat.subcategories.filter(active=True).order_by('order', 'name'))
        groups = OrderedDict()
        for s in subs:
            grp = s.menu_group.strip() if s.menu_group else 'SHOP BY STYLE'
            if grp not in groups:
                groups[grp] = []
            groups[grp].append(s)
        cat.mega_groups = list(groups.items())
        cat.active_subcategories = subs

    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'global_categories': main_cats,
        'store_currency': '₹',
        'free_shipping_threshold': 999,
    }
