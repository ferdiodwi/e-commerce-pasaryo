from django.contrib import admin

from .models import Payment, PaymentMethod


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
        "order",
        "payment_method",
    )

    date_hierarchy = "paid_at"
    ordering = ("-id",)
    list_per_page = 25

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