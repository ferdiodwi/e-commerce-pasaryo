from django import forms

from .models import DiscountType, Event, EventProduct


# Form Event di admin
class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ("products",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Batasi pilihan tipe diskon event ke Persentase
        self.fields["discount_type"].choices = [
            (DiscountType.PERCENTAGE, DiscountType.PERCENTAGE.label),
        ]


# Form inline produk event
class EventProductInlineForm(forms.ModelForm):
    class Meta:
        model = EventProduct
        fields = ("product", "discount_type", "discount_value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opsi kosong untuk ikut diskon event, atau pilih Persentase
        self.fields["discount_type"].choices = [
            ("", "---------"),
            (DiscountType.PERCENTAGE, DiscountType.PERCENTAGE.label),
        ]
