from django import forms
from django.core.exceptions import ValidationError

from .models import ProductVariant
from .services import validate_stock_adjustment


# Form varian produk & atur stok
class ProductVariantAdminForm(forms.ModelForm):
    # Input penyesuaian stok (+/-)
    stock_adjustment = forms.IntegerField(
        label="Penyesuaian stok",
        required=False,
        initial=0,
        help_text=(
            "Isi 10 untuk menambah 10 unit, "
            "-2 untuk mengurangi 2 unit."
        ),
    )

    # Alasan ubah stok
    stock_note = forms.CharField(
        label="Alasan penyesuaian",
        max_length=200,
        required=False,
    )

    class Meta:
        model = ProductVariant
        fields = (
            "product",
            "color_name",
            "sku",
        )

    # Validasi penyesuaian stok
    def clean(self):
        cleaned_data = super().clean()
        adjustment = cleaned_data.get("stock_adjustment") or 0
        current_stock = 0

        if self.instance.pk:
            current = (
                ProductVariant.objects.select_for_update()
                .filter(pk=self.instance.pk)
                .first()
            )

            if current is None:
                raise ValidationError("Varian sudah dihapus.")

            current_stock = current.stock

        try:
            validate_stock_adjustment(
                current_stock,
                adjustment,
            )
        except ValidationError as error:
            self.add_error("stock_adjustment", error)

        # Wajib isi alasan jika ubah stok
        if adjustment and not cleaned_data.get("stock_note"):
            self.add_error(
                "stock_note",
                "Isi alasan penyesuaian stok.",
            )

        return cleaned_data
