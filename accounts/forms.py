from django.contrib.auth.forms import (
    BaseUserCreationForm,
    UserChangeForm,
)

from .models import User


class AccountCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "phone",
            "role",
            "date_of_birth",
            "is_active",
        )


class AccountChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"