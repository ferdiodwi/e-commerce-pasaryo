from django.contrib import admin

from .forms import PaymentAdminForm
from .models import Payment, PaymentMethod
from .services import save_payment


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "channel_provider",
        "service_fee",
        "is_active",
    )

    list_display_links = ("id",)

    search_fields = (
        "name",
        "channel_provider",
    )

    list_filter = ("is_active",)

    ordering = ("name", "id")
    list_per_page = 25


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm

    list_display = (
        "id",
        "payment_reference",
        "order",
        "payment_method",
        "payment_amount",
        "payment_status",
        "paid_at",
    )

    list_display_links = ("id",)

    search_fields = (
        "payment_reference",
        "order__order_number",
        "order__user__email",
    )

    list_filter = (
        "payment_status",
        "payment_method",
    )

    list_select_related = (
        "order",
        "payment_method",
    )

    autocomplete_fields = (
        "payment_method",
    )

    date_hierarchy = "paid_at"
    ordering = ("-id",)
    list_per_page = 25

    readonly_fields = (
        "order",
    )

    fieldsets = (
        (
            "Pesanan",
            {
                "fields": (
                    "order",
                    "payment_reference",
                ),
            },
        ),
        (
            "Pembayaran",
            {
                "fields": (
                    "payment_method",
                    "payment_amount",
                    "payment_status",
                ),
            },
        ),
        (
            "Waktu dan tautan",
            {
                "fields": (
                    "expires_at",
                    "paid_at",
                    "payment_url",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        save_payment(obj)
