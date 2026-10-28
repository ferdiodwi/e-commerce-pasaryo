from django.contrib import admin

from .models import ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "estimated_days",
        "base_cost",
        "is_active",
    )

    list_display_links = ("id",)
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)
    list_per_page = 25