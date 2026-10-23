from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.accounts.models import User
from apps.common.admin import BaseAdmin

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin[User], BaseAdmin):
    """Users with Unfold forms; email is the login."""

    list_select_related = ("region", "district")
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    ordering = ("-date_joined",)
    list_display = ("email", "region", "district", "ui_language", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_active", "ui_language", "region")
    search_fields = ("email", "display_name")
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "ui_language", "region", "district")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
    autocomplete_fields = ("region", "district")


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, BaseAdmin):
    """Groups with the Unfold look."""

    readonly_fields = ()
