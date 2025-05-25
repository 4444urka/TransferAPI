from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from apps.auth.models import User
from apps.auth.services import UserService
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError


class CustomUserChangeForm(UserChangeForm):
    """
    Кастомная форма изменения пользователя в админке.
    Использует UserService для валидации поля chat_id.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
        self.fields['phone_number'].disabled = True

    def clean_chat_id(self):
        chat_id = self.cleaned_data.get('chat_id')
        
        if not chat_id:
            return chat_id
            
        user_id = self.instance.id if self.instance else None
        try:
            return self.user_service.validate_chat_id(chat_id, user_id=user_id)
        except serializers.ValidationError as e:
            chat_errors = e.detail.get('chat_id')
            raise DjangoValidationError(chat_errors or 'Invalid chat_id')


    class Meta:
        model = User
        fields = ('phone_number', 'chat_id', 'first_name', 'last_name', 'password')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number', 'first_name', 'last_name', 'password')

class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Персональная информация', {'fields': ('phone_number', 'first_name', 'last_name', 'chat_id')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    list_display = ('id','phone_number', 'chat_id', 'first_name', 'last_name', 'is_staff')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('phone_number',)

admin.site.register(User, CustomUserAdmin)