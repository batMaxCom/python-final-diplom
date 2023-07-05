from django.contrib import admin
from users import models
from users.models import Contact


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'last_login',
                    'is_active', 'is_staff', 'is_superuser', 'type')
    fields = ('company', 'position', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'code', 'type')
    list_display_links = ('email',)
    readonly_fields = ('last_login', 'email', )
    search_fields = ('email', 'first_name', 'last_name',)
    list_filter = (
        ('is_active', admin.BooleanFieldListFilter),
        ('is_staff', admin.BooleanFieldListFilter),
        ('is_superuser', admin.BooleanFieldListFilter),
        ('last_login', admin.DateFieldListFilter),
    )

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Contact._meta.fields]