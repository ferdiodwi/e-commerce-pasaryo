from django.contrib import admin

from .models import Event, EventProduct


class EventProductInline(admin.TabularInline):
    model = EventProduct
    fields = ("product", "discount_type", "discount_value")
    autocomplete_fields = ("product",)
    extra = 1

    verbose_name = "Produk event"
    verbose_name_plural = "Produk event"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
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