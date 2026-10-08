from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for Customer management.
    """
    list_display = (
        'customer_code',
        'name',
        'email',
        'phone',
        'company_name',
        'credit_limit',
        'outstanding_balance',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'country',
        'created_at',
    )
    search_fields = (
        'customer_code',
        'name',
        'email',
        'phone',
        'company_name',
        'tax_id',
    )
    readonly_fields = (
        'customer_code',
        'created_at',
        'updated_at',
        'available_credit_display',
    )
    fieldsets = (
        ('Customer Core Information', {
            'fields': (
                'customer_code',
                'name',
                'company_name',
                'is_active',
                'distributor',
            )
        }),
        ('Contact Details', {
            'fields': (
                'email',
                'phone',
            )
        }),
        ('Address & Location', {
            'fields': (
                'address',
                'city',
                'state',
                'postal_code',
                'country',
            )
        }),
        ('Financial & Billing Settings', {
            'fields': (
                'tax_id',
                'credit_limit',
                'outstanding_balance',
                'available_credit_display',
            )
        }),
        ('Additional Notes & Audit Trail', {
            'fields': (
                'notes',
                'created_at',
                'updated_at',
            )
        }),
    )

    def available_credit_display(self, obj):
        if obj.pk:
            return f"${obj.available_credit:,.2f}"
        return "$0.00"
    available_credit_display.short_description = "Available Credit ($)"
