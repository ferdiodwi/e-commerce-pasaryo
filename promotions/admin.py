from django.contrib import admin

from .forms import EventAdminForm, EventProductInlineForm
from .models import Discount, Event, EventProduct, PromoCode


# Tabel inline produk event
class EventProductInline(admin.TabularInline):
    model = EventProduct
    form = EventProductInlineForm
    fields = ("product", "discount_type", "discount_value")
    autocomplete_fields = ("product",)
    extra = 1

    verbose_name = "Produk event"
    verbose_name_plural = "Produk event"


# Daftarkan Event ke admin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = (
        "id",
        "name",
        "start_date",
        "end_date",
        "discount_type",
        "discount_value",
    )

    list_display_links = ("id",)
    search_fields = ("name",)
    list_filter = ("discount_type",)
    ordering = ("-start_date", "-id")
    list_per_page = 25

    exclude = ("products",)
    inlines = (EventProductInline,)


# Daftarkan Discount ke admin
@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "discount_value",
        "start_date",
        "end_date",
    )

    list_display_links = ("id",)
    search_fields = ("product__name",)
    list_filter = ("product__category", "product__brand")
    autocomplete_fields = ("product",)
    list_select_related = ("product",)

    ordering = ("-start_date", "-id")
    list_per_page = 25


# Daftarkan PromoCode ke admin
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "discount_type",
        "discount_value",
        "quota_total",
        "is_active",
        "expires_at",
    )

    list_display_links = ("id",)
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active")

    ordering = ("-id",)
    list_per_page = 25
