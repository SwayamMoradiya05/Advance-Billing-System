from django.contrib import admin
from django.utils.html import format_html
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Django Admin interface for managing Products and Inventory in Advance Billing System.
    """
    list_display = [
        'sku',
        'name',
        'category',
        'price_display',
        'gst_rate_display',
        'price_with_gst_display',
        'stock',
        'unit',
        'stock_status_badge',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'category',
        'gst_rate',
        'is_active',
        'unit',
        'created_at',
    ]
    search_fields = [
        'sku',
        'name',
        'category',
        'hsn_code',
        'description',
    ]
    list_editable = [
        'stock',
        'is_active',
    ]
    readonly_fields = [
        'sku',
        'gst_amount',
        'price_with_gst',
        'total_stock_value',
        'total_stock_value_with_gst',
        'stock_status',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('sku', 'name', 'category', 'description', 'is_active')
        }),
        ('Pricing & Tax Details', {
            'fields': (
                'price',
                'gst_rate',
                'gst_amount',
                'price_with_gst',
                'hsn_code',
            )
        }),
        ('Inventory Management', {
            'fields': (
                'stock',
                'unit',
                'min_stock_level',
                'stock_status',
                'total_stock_value',
                'total_stock_value_with_gst',
            )
        }),
        ('Audit Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description="Price (Excl. GST)", ordering="price")
    def price_display(self, obj):
        return f"₹{obj.price:,.2f}"

    @admin.display(description="GST Rate", ordering="gst_rate")
    def gst_rate_display(self, obj):
        return f"{obj.gst_rate}%"

    @admin.display(description="Price (Incl. GST)")
    def price_with_gst_display(self, obj):
        return f"₹{obj.price_with_gst:,.2f}"

    @admin.display(description="Stock Status")
    def stock_status_badge(self, obj):
        status = obj.stock_status
        if status == 'Out of Stock':
            color = 'danger'
        elif status == 'Low Stock':
            color = 'warning'
        else:
            color = 'success'
        return format_html(
            '<span class="badge bg-{}" style="padding: 5px 10px; font-weight: 600;">{}</span>',
            color,
            status
        )
