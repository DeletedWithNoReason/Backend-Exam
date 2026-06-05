from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('phone', 'email', 'first_name', 'last_name', 'role')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    add_form = CustomUserCreationForm

    list_display = ('phone', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('phone', 'email', 'first_name', 'last_name')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
    )


    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'last_name', 'email',
                       'role','password1', 'password2')
        }),
    )