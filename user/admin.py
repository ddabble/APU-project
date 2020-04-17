from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models.functions import Concat

from .models import Profile


class CustomUserAdmin(UserAdmin):
    class ProfileInline(admin.StackedInline):
        model = Profile
        can_delete = False
        verbose_name_plural = 'Profile'
        fk_name = 'user'

    inlines = (ProfileInline,)

    #                                    Removes 'is_staff'
    list_display = UserAdmin.list_display[:-1] + ('get_company', 'is_active')
    list_select_related = ('profile',)
    list_editable = ('is_active',)

    def get_company(self, user):
        return user.profile.company

    get_company.admin_order_field = 'profile__company'
    get_company.short_description = 'Company'


class ProfileAdmin(admin.ModelAdmin):
    """
    Only used by `raw_id_fields` in other model admins.
    """
    list_display = ('user', 'get_full_name', 'company', 'country', 'state', 'city')
    list_select_related = ('user',)
    list_filter = ('company', 'country')
    search_fields = [f'user__{f}' for f in UserAdmin.search_fields] + ['company']

    def get_full_name(self, profile):
        return profile.user.get_full_name()

    get_full_name.admin_order_field = Concat('user__first_name', 'user__last_name')
    get_full_name.short_description = 'Full name'

    def get_model_perms(self, request):
        # Hides model admin from admin list
        return {}


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
