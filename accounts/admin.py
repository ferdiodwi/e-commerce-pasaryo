from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import AccountChangeForm, AccountCreationForm
from .models import User, UserAddress


# Daftarkan User ke admin
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Form edit user
    form = AccountChangeForm
    # Form tambah user
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

    # Kolom read-only
    readonly_fields = (
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    filter_horizontal = ()

    # Tata letak form edit user
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

    # Tata letak form tambah user
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


# Daftarkan UserAddress ke admin
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
    # Optimasi query user
    list_select_related = ("user",)
    ordering = ("-id",)
    list_per_page = 25

    # Matikan izin tambah, edit, dan hapus
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
