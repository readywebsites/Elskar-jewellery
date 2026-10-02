from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Wishlist, Address, Order, OrderItem, ContactInquiry, NewsletterSubscriber
)

# Customize Admin Site Headers for Azure Jewels
admin.site.site_header = "Azure Jewels | Luxury Fine Jewellery Admin"
admin.site.site_title = "Azure Jewels Admin Portal"
admin.site.index_title = "E-Commerce Management & Store Analytics"

from django.db.models import Sum
from django.contrib.auth.models import User

from django.shortcuts import render
from store.admin_views import get_admin_dashboard_context

original_admin_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return original_admin_index(request, extra_context=extra_context)
    
    ctx = get_admin_dashboard_context(request)
    try:
        ctx['app_list'] = admin.site.get_app_list(request)
    except Exception:
        pass
    if extra_context:
        ctx.update(extra_context)
    return render(request, 'admin-dashboard.html', ctx)

admin.site.index = custom_admin_index



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'parent', 'menu_group', 'order', 'slug', 'active', 'created_at')
    list_filter = ('parent', 'menu_group', 'active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('menu_group', 'order', 'active')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:cover; border-radius:3px; border:1px solid #D9E3EC;" />', obj.image.url)
        return format_html('<span style="color:#888; font-size:11px;">—</span>')
    image_preview.short_description = 'Thumbnail'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'category', 'subcategory', 'sku', 'price', 'sale_price', 'stock',
        'featured', 'best_seller', 'new_arrival', 'active'
    )
    list_filter = ('category', 'subcategory', 'featured', 'best_seller', 'new_arrival', 'active', 'created_at')
    search_fields = ('name', 'sku', 'description', 'material')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'sale_price', 'stock', 'featured', 'best_seller', 'new_arrival', 'active')
    inlines = [ProductImageInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="44" height="44" style="object-fit:cover; border-radius:3px; border:1px solid #D9E3EC;" />', obj.image.url)
        return format_html('<span style="color:#888; font-size:11px;">—</span>')
    image_preview.short_description = 'Thumbnail'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'name', 'price', 'quantity', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'full_name', 'email', 'phone', 'total',
        'payment_method', 'payment_status', 'status', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'full_name', 'email', 'phone', 'address')
    list_editable = ('status', 'payment_status')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'total_price')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'total_items', 'subtotal', 'shipping_fee', 'total', 'created_at')
    inlines = [CartItemInline]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone', 'city', 'state', 'postal_code', 'is_default', 'created_at')
    list_filter = ('is_default', 'state', 'city')
    search_fields = ('full_name', 'phone', 'city', 'postal_code', 'user__username')


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_resolved',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
