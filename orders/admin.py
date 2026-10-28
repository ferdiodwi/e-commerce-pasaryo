from django.contrib import admin

from .forms import OrderItemInlineFormSet
from .models import Order, OrderItem, ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "estimated_days", "base_cost", "is_active",
    )
    list_display_links = ("id",)
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)
    list_per_page = 25


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    formset = OrderItemInlineFormSet
    autocomplete_fields = ("product_variant",)
    extra = 1

    fields = (
        "product_variant",
        "product_name_snapshot",
        "variant_name_snapshot",
        "sku_snapshot",
        "quantity",
        "price_at_purchase",
    )
    readonly_fields = (
        "product_name_snapshot",
        "variant_name_snapshot",
        "sku_snapshot",
        "price_at_purchase",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "user",
        "status",
        "total_amount",
        "created_at",
    )
    list_display_links = ("id",)
    search_fields = ("order_number", "user__email")
    list_filter = ("status", "shipping_method")
    list_select_related = ("user", "shipping_method", "promo_code")
    autocomplete_fields = ("user", "shipping_method", "promo_code")
    ordering = ("-created_at", "-id")
    list_per_page = 25

    readonly_fields = ("subtotal", "total_amount", "created_at")
    inlines = (OrderItemInline,)

    fieldsets = (
        (
            "Pesanan",
            {
                "fields": (
                    "order_number",
                    "user",
                    "status",
                    "promo_code",
                    "created_at",
                )
            },
        ),
        (
            "Pengiriman",
            {
                "fields": (
                    "shipping_method",
                    "shipping_address_snapshot",
                    "estimated_delivery_from",
                    "estimated_delivery_to",
                )
            },
        ),
        (
            "Tagihan",
            {
                "fields": (
                    "subtotal",
                    "shipping_fee",
                    "service_fee",
                    "discount_amount",
                    "total_amount",
                    "payment_due_at",
                )
            },
        ),
    )