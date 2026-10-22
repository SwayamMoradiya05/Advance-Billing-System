from django.contrib import admin

from .models import DistributorProfile


@admin.register(DistributorProfile)
class DistributorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'distributor_id',
        'user',
        'company_name',
        'phone',
        'credit_limit',
        'is_verified',
        'created_at',
    )
    list_filter = ('is_verified', 'created_at')
    search_fields = (
        'distributor_id',
        'company_name',
        'phone',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at',)
