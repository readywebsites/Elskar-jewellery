from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Catalog & Shop
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('category/<slug:category_slug>/', views.category_view, name='category_detail'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.category_view, name='subcategory_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_view, name='search'),

    # Cart
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),

    # Wishlist
    path('wishlist/', views.wishlist_detail, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/move-to-cart/<int:product_id>/', views.wishlist_move_to_cart, name='wishlist_move_to_cart'),

    # Checkout & Orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),

    # Authentication & Accounts
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('account/dashboard/', views.account_dashboard, name='account_dashboard'),
    path('account/orders/', views.account_orders, name='account_orders'),
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/addresses/', views.account_addresses, name='account_addresses'),
    path('account/addresses/delete/<int:address_id>/', views.address_delete, name='address_delete'),
    path('account/addresses/default/<int:address_id>/', views.address_set_default, name='address_set_default'),

    # Informational, Policies & Contact
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('store-locator/', views.store_locator_view, name='store_locator'),
    path('stores/', views.store_locator_view, name='stores'),
    path('track-package/', views.track_package_view, name='track_package'),
    path('track-order/', views.track_package_view, name='track_order'),
    path('track/', views.track_package_view, name='track'),
    path('faq/', views.faq_view, name='faq'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms_view, name='terms'),
    path('terms-conditions/', views.terms_view, name='terms_conditions'),
    path('returns/', views.returns_view, name='returns'),
    path('return-policy/', views.returns_view, name='return_policy'),
    path('shipping-policy/', views.shipping_policy_view, name='shipping_policy'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # Admin Management Dashboard & Executive Atelier Suite
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard_alt'),
    path('admin-dashboard/order/<int:order_id>/status/', views.admin_order_update_status, name='admin_order_update_status'),
    path('admin-dashboard/order/<int:order_id>/details/', views.admin_order_detail_api, name='admin_order_detail_api'),
    path('admin-dashboard/product/add/', views.admin_product_create, name='admin_product_create'),
    path('admin-dashboard/product/<int:product_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-dashboard/product/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-dashboard/product/<int:product_id>/toggle-active/', views.admin_product_toggle_active, name='admin_product_toggle_active'),
    path('admin-dashboard/product/<int:product_id>/stock/', views.admin_product_quick_stock, name='admin_product_quick_stock'),
    path('admin-dashboard/product/gallery-image/<int:image_id>/delete/', views.admin_gallery_image_delete, name='admin_gallery_image_delete'),
    path('admin-dashboard/category/add/', views.admin_category_create, name='admin_category_create'),
    path('admin-dashboard/category/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    path('admin-dashboard/inquiry/<int:inquiry_id>/toggle/', views.admin_inquiry_toggle, name='admin_inquiry_toggle'),

    # APIs & Headless Integration Endpoints
    path('api/dashboard/', views.api_admin_dashboard, name='api_admin_dashboard'),
    path('api/admin/status/', views.api_admin_status, name='api_admin_status'),
    path('api/admin/login/', views.api_admin_login, name='api_admin_login'),
    path('api/admin/logout/', views.api_admin_logout, name='api_admin_logout'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/categories/<int:category_id>/', views.api_category_detail, name='api_category_detail'),
    path('api/products/', views.products_api, name='api_products'),
    path('api/products/<int:product_id>/', views.api_product_detail, name='api_product_detail'),
    path('api/orders/', views.api_admin_orders, name='api_admin_orders'),
    path('api/orders/<int:order_id>/status/', views.api_admin_order_status, name='api_admin_order_status'),

    # Legacy Compatibility URL Redirections (prevents 404s for hardcoded .html links)
    path('admin.html', views.admin_dashboard_view, name='admin_html'),

    path('index.html', RedirectView.as_view(pattern_name='home', permanent=True)),
    path('shop-grid.html', RedirectView.as_view(pattern_name='shop', permanent=True)),
    path('shop-grid-type-4.html', RedirectView.as_view(pattern_name='shop', permanent=True)),
    path('shop-grid-type-5.html', RedirectView.as_view(pattern_name='shop', permanent=True)),
    path('cart.html', RedirectView.as_view(pattern_name='cart', permanent=True)),
    path('wishlist.html', RedirectView.as_view(pattern_name='wishlist', permanent=True)),
    path('checkout.html', RedirectView.as_view(pattern_name='checkout', permanent=True)),
    path('billing-details.html', RedirectView.as_view(pattern_name='checkout', permanent=True)),
    path('thank-you.html', RedirectView.as_view(pattern_name='home', permanent=False)),
    path('account-dashboard.html', RedirectView.as_view(pattern_name='account_dashboard', permanent=True)),
    path('account-orders.html', RedirectView.as_view(pattern_name='account_orders', permanent=True)),
    path('account-profile.html', RedirectView.as_view(pattern_name='account_profile', permanent=True)),
    path('account-edit-profile.html', RedirectView.as_view(pattern_name='account_profile', permanent=True)),
    path('account-saved-address.html', RedirectView.as_view(pattern_name='account_addresses', permanent=True)),
    path('address.html', RedirectView.as_view(pattern_name='account_addresses', permanent=True)),
    path('authentication-login.html', RedirectView.as_view(pattern_name='login', permanent=True)),
    path('authentication-register.html', RedirectView.as_view(pattern_name='register', permanent=True)),
    path('authentication-reset-password.html', RedirectView.as_view(pattern_name='password_reset', permanent=True)),
    path('about-us.html', RedirectView.as_view(pattern_name='about', permanent=True)),
    path('contact-us.html', RedirectView.as_view(pattern_name='contact', permanent=True)),
    path('returns.html', RedirectView.as_view(pattern_name='returns', permanent=True)),
    path('store-locator.html', RedirectView.as_view(pattern_name='store_locator', permanent=True)),
    path('stores.html', RedirectView.as_view(pattern_name='store_locator', permanent=True)),
    path('track-package.html', RedirectView.as_view(pattern_name='track_package', permanent=True)),
    path('track.html', RedirectView.as_view(pattern_name='track_package', permanent=True)),
    path('track-order.html', RedirectView.as_view(pattern_name='track_package', permanent=True)),
    path('terms.html', RedirectView.as_view(pattern_name='terms', permanent=True)),
    path('privacy-policy.html', RedirectView.as_view(pattern_name='privacy_policy', permanent=True)),
    path('shipping-policy.html', RedirectView.as_view(pattern_name='shipping_policy', permanent=True)),
    path('faq.html', RedirectView.as_view(pattern_name='faq', permanent=True)),
    path('collections.html', RedirectView.as_view(pattern_name='shop', permanent=True)),
    path('search.html', RedirectView.as_view(pattern_name='shop', permanent=True)),
]
