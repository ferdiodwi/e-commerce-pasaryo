from django.contrib import admin

from .models import Brand, Category


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25