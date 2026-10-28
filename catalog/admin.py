from django.contrib import admin

from .models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


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


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ("image_url", "sort_order")
    ordering = ("sort_order",)
    extra = 1

    verbose_name = "Gambar produk"
    verbose_name_plural = "Gambar produk"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    fields = ("color_name", "sku", "stock")
    extra = 1

    verbose_name = "Varian produk"
    verbose_name_plural = "Varian produk"
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "brand",
        "price",
        "origin_city",
    )

    list_display_links = ("id",)

    search_fields = (
        "name",
        "category__name",
        "brand__name",
        "origin_city",
    )

    list_filter = ("category", "brand", "origin_city")
    list_select_related = ("category", "brand")
    autocomplete_fields = ("category", "brand")

    ordering = ("-id",)
    list_per_page = 25

    fields = (
        "name",
        "category",
        "brand",
        "description",
        "specifications",
        "price",
        "origin_city",
    )

    inlines = (
        ProductImageInline,
        ProductVariantInline,
    )



@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "color_name", "sku", "stock")
    list_display_links = ("id",)
    search_fields = ("sku", "product__name", "color_name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)
    ordering = ("-id",)
    list_per_page = 25