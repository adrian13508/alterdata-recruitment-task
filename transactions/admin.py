from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id',
        'timestamp',
        'amount',
        'currency',
        'customer_id',
        'product_id',
        'quantity',
        'created_at'
    ]
    list_filter = ['currency', 'timestamp', 'created_at']
    search_fields = ['transaction_id', 'customer_id', 'product_id']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'timestamp', 'amount', 'currency', 'quantity')
        }),
        ('Related IDs', {
            'fields': ('customer_id', 'product_id')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
