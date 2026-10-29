from django.contrib import admin

from .forms import ProductVariantAdminForm
from .models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)
from .services import save_product_variant


# Daftarkan Brand ke admin
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25


# Daftarkan Category ke admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25


# Tabel inline gambar produk
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ("image_url", "sort_order")
    ordering = ("sort_order",)
    extra = 1

    verbose_name = "Gambar produk"
    verbose_name_plural = "Gambar produk"


# Tabel inline varian produk
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    fields = ("color_name", "sku", "stock")
    # Stok dibuat read-only di inline
    readonly_fields = ("stock",)
    extra = 1

    verbose_name = "Varian produk"
    verbose_name_plural = "Varian produk"


# Daftarkan Product ke admin
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
    # Optimasi query relasi
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

    # Simpan inline varian lewat service
    def save_formset(self, request, form, formset, change):
        if formset.model is not ProductVariant:
            return super().save_formset(request, form, formset, change)

        instances = formset.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        for instance in instances:
            save_product_variant(instance)

        formset.save_m2m()


# Daftarkan ProductVariant ke admin
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    form = ProductVariantAdminForm

    list_display = ("id", "product", "color_name", "sku", "stock")
    list_display_links = ("id",)
    search_fields = ("sku", "product__name", "color_name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)
    ordering = ("-id",)
    list_per_page = 25

    # Stok dibuat read-only (ubah lewat stock_adjustment)
    readonly_fields = ("stock",)

    fields = (
        "product",
        "color_name",
        "sku",
        "stock",
        "stock_adjustment",
        "stock_note",
    )

    # Simpan perubahan stok lewat service
    def save_model(self, request, obj, form, change):
        save_product_variant(
            obj,
            adjustment=(
                form.cleaned_data.get("stock_adjustment") or 0
            ),
        )

    # Catat riwayat ubah stok ke History admin
    def construct_change_message(
        self,
        request,
        form,
        formsets,
        add=False,
    ):
        message = super().construct_change_message(
            request,
            form,
            formsets,
            add,
        )
        adjustment = (
            form.cleaned_data.get("stock_adjustment") or 0
        )

        if adjustment:
            obj = form.instance
            note = form.cleaned_data["stock_note"]
            message.append(
                {
                    "changed": {
                        "fields": [
                            f"Stok {obj._stock_before} "
                            f"menjadi {obj.stock} "
                            f"({adjustment:+d}); alasan: {note}"
                        ],
                    },
                }
            )

        return message
