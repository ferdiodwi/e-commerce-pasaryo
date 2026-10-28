from django.contrib import admin

from .forms import OrderAdminForm, OrderTrackingAdminForm
from .models import (
    Order,
    OrderItem,
    OrderTracking,
    Review,
    ShippingMethod,
)
from .services import sync_order_tracking


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
    extra = 0
    can_delete = False

    fields = (
        "product_variant",
        "product_name_snapshot",
        "variant_name_snapshot",
        "sku_snapshot",
        "quantity",
        "price_at_purchase",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    form = OrderTrackingAdminForm
    can_delete = False

    fields = (
        "status_code",
        "description",
        "event_time",
        "expected_time",
        "is_completed",
    )

    extra = 0
    ordering = ("event_time", "id")

    verbose_name = "Riwayat pesanan"
    verbose_name_plural = "Riwayat pesanan"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm

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

    list_select_related = (
        "user",
        "shipping_method",
        "promo_code",
    )

    ordering = ("-created_at", "-id")
    list_per_page = 25

    readonly_fields = (
        "order_number",
        "user",
        "promo_code",
        "created_at",
        "shipping_method",
        "shipping_address_snapshot",
        "subtotal",
        "shipping_fee",
        "service_fee",
        "discount_amount",
        "total_amount",
        "payment_due_at",
    )

    inlines = (
        OrderItemInline,
        OrderTrackingInline,
    )

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
                ),
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
                ),
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
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        if change and "status" in form.changed_data:
            sync_order_tracking(form.instance)


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    form = OrderTrackingAdminForm

    list_display = (
        "id",
        "order",
        "status_code",
        "description",
        "event_time",
        "expected_time",
        "is_completed",
    )

    list_display_links = ("id",)

    search_fields = (
        "order__order_number",
        "order__user__email",
        "description",
    )

    list_filter = (
        "status_code",
        "is_completed",
    )

    list_select_related = ("order",)
    autocomplete_fields = ("order",)

    date_hierarchy = "event_time"
    ordering = ("-event_time", "-id")
    list_per_page = 25

    fields = (
        "order",
        "status_code",
        "description",
        "event_time",
        "expected_time",
        "is_completed",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_item",
        "customer_email",
        "rating",
        "created_at",
    )

    list_display_links = ("id",)

    search_fields = (
        "order_item__order__order_number",
        "order_item__order__user__email",
        "order_item__product_name_snapshot",
        "order_item__sku_snapshot",
        "comment",
    )

    list_filter = ("rating",)

    list_select_related = (
        "order_item__order__user",
    )

    readonly_fields = (
        "order_item",
        "rating",
        "comment",
        "created_at",
    )

    fields = (
        "order_item",
        "rating",
        "comment",
        "created_at",
    )

    date_hierarchy = "created_at"
    ordering = ("-created_at", "-id")
    list_per_page = 25

    @admin.display(
        description="Pelanggan",
        ordering="order_item__order__user__email",
    )
    def customer_email(self, obj):
        return obj.order_item.order.user.email

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
