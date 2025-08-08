from django.contrib import admin
from .models import ApiToken


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'last_used_at', 'token_preview']
    list_filter = ['is_active', 'created_at', 'last_used_at']
    search_fields = ['name', 'token']
    readonly_fields = ['created_at', 'last_used_at']

    def token_preview(self, obj):
        return f"{obj.token[:8]}..." if obj.token else ""

    token_preview.short_description = 'Token Preview'