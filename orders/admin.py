from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .forms import OrderAdminForm, OrderTrackingAdminForm
from .models import (
    Order,
    OrderItem,
    OrderTracking,
    Review,
    ShippingMethod,
)
from .services import sync_order_tracking, validate_order_status


# Daftarkan ShippingMethod ke admin
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


# Inline item pesanan (Read-Only)
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


# Inline riwayat pelacakan
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


# Daftarkan Order ke admin
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

    list_display_links = ("id", "order_number")
    # Edit status langsung dari tabel
    list_editable = ("status",)
    actions = ("mark_as_shipped",)

    search_fields = ("order_number", "user__email")
    list_filter = ("status", "shipping_method")

    list_select_related = (
        "user",
        "shipping_method",
        "promo_code",
    )

    ordering = ("-created_at", "-id")
    list_per_page = 25

    # Data transaksi dibuat read-only
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

    # Tata letak form pesanan
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

    # Pasang validasi status pada list_editable di tabel
    def get_changelist_form(self, request, **kwargs):
        kwargs.setdefault("form", OrderAdminForm)
        return super().get_changelist_form(request, **kwargs)

    # Order hanya dibuat via checkout pembeli
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    # Sinkronkan tracking saat status berubah
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if change and "status" in form.changed_data:
            sync_order_tracking(obj)

    # Aksi massal ubah status ke Shipped
    @admin.action(description="Ubah status pesanan terpilih menjadi Shipped")
    def mark_as_shipped(self, request, queryset):
        updated_count = 0
        for order in queryset:
            try:
                with transaction.atomic():
                    locked = Order.objects.select_for_update().get(pk=order.pk)
                    if locked.status == Order.Status.SHIPPED:
                        continue
                    validate_order_status(locked, Order.Status.SHIPPED)
                    locked.status = Order.Status.SHIPPED
                    locked.save(update_fields=["status"])
                    sync_order_tracking(locked)
                    updated_count += 1
            except ValidationError as exc:
                err_text = "; ".join(exc.messages)
                self.message_user(
                    request,
                    f"{order.order_number}: {err_text}",
                    level=messages.ERROR,
                )

        if updated_count:
            self.message_user(
                request,
                f"{updated_count} pesanan berhasil diubah ke status Shipped.",
                level=messages.SUCCESS,
            )


# Daftarkan OrderTracking ke admin
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

    # Riwayat pelacakan tidak boleh dihapus
    def has_delete_permission(self, request, obj=None):
        return False


# Daftarkan Review ke admin (Read-Only)
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

    # Tampilkan email pembeli
    @admin.display(
        description="Pelanggan",
        ordering="order_item__order__user__email",
    )
    def customer_email(self, obj):
        return obj.order_item.order.user.email

    # Admin tidak boleh menambah atau mengedit review pembeli
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
