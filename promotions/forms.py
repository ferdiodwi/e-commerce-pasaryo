from django import forms

from .models import DiscountType, Event, EventProduct


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ("products",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["discount_type"].choices = [
            (DiscountType.PERCENTAGE, DiscountType.PERCENTAGE.label),
        ]


class EventProductInlineForm(forms.ModelForm):
    class Meta:
        model = EventProduct
        fields = ("product", "discount_type", "discount_value")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["discount_type"].choices = [
            ("", "---------"),
            (DiscountType.PERCENTAGE, DiscountType.PERCENTAGE.label),
        ]

