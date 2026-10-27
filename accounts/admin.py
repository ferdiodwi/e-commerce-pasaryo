from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import AccountChangeForm, AccountCreationForm
from .models import User, UserAddress


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = AccountChangeForm
    add_form = AccountCreationForm

    list_display = (
        "id",
        "full_name",
        "email",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("full_name", "email", "phone")
    list_filter = ("role", "is_active")
    ordering = ("-date_joined", "-id")
    list_per_page = 25

    readonly_fields = (
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    filter_horizontal = ()

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profil",
            {"fields": ("full_name", "phone", "date_of_birth")},
        ),
        (
            "Akses",
            {"fields": ("role", "is_active", "is_staff", "is_superuser")},
        ),
        (
            "Riwayat",
            {"fields": ("date_joined", "last_login")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "date_of_birth",
                    "role",
                    "is_active",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "label",
        "recipient_name",
        "city",
        "is_main",
    )
    search_fields = (
        "user__email",
        "recipient_name",
        "recipient_phone",
        "street_address",
        "city",
    )
    list_filter = ("province", "city", "is_main")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
    ordering = ("-id",)
    list_per_page = 25