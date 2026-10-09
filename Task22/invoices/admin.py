from django.contrib import admin
from django.utils.html import format_html
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'gst_rate', 'discount_percentage', 'line_subtotal', 'tax_amount', 'total_amount')
    readonly_fields = ('line_subtotal', 'tax_amount', 'total_amount')
    autocomplete_fields = ('product',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_link', 'invoice_date', 'due_date', 'colored_status', 'grand_total_formatted', 'balance_due_formatted')
    list_filter = ('status', 'payment_method', 'invoice_date', 'due_date')
    search_fields = ('invoice_number', 'customer__name', 'customer__customer_code', 'customer__email')
    readonly_fields = ('invoice_number', 'subtotal', 'tax_amount', 'grand_total', 'balance_due', 'created_at', 'updated_at')
    autocomplete_fields = ('customer', 'created_by')
    inlines = [InvoiceItemInline]
    date_hierarchy = 'invoice_date'
    actions = ['recalculate_selected_invoices', 'mark_as_paid', 'mark_as_pending']
    
    fieldsets = (
        ('Invoice General Information', {
            'fields': ('invoice_number', 'customer', 'created_by', 'status', 'payment_method', 'payment_terms')
        }),
        ('Dates & Timeline', {
            'fields': ('invoice_date', 'due_date')
        }),
        ('Financial Summary', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'grand_total', 'amount_paid', 'balance_due')
        }),
        ('Notes & Terms', {
            'classes': ('collapse',),
            'fields': ('notes', 'terms_and_conditions')
        }),
        ('System Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def customer_link(self, obj):
        if obj.customer:
            return f"{obj.customer.name} ({obj.customer.customer_code})"
        return "-"
    customer_link.short_description = "Customer"

    def grand_total_formatted(self, obj):
        return f"₹{obj.grand_total}"
    grand_total_formatted.short_description = "Grand Total"

    def balance_due_formatted(self, obj):
        return f"₹{obj.balance_due}"
    balance_due_formatted.short_description = "Balance Due"

    def colored_status(self, obj):
        colors = {
            'DRAFT': '#6c757d',
            'PENDING': '#ffc107',
            'PAID': '#28a745',
            'PARTIALLY_PAID': '#17a2b8',
            'CANCELLED': '#dc3545',
            'OVERDUE': '#e83e8c',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = "Status"

    @admin.action(description="Recalculate financial totals for selected invoices")
    def recalculate_selected_invoices(self, request, queryset):
        count = 0
        for invoice in queryset:
            invoice.calculate_totals(save_instance=True)
            count += 1
        self.message_user(request, f"Successfully recalculated totals for {count} invoice(s).")

    @admin.action(description="Mark selected invoices as PAID")
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='PAID', amount_paid=models.F('grand_total'))
        self.message_user(request, f"Successfully marked {updated} invoice(s) as PAID.")

    @admin.action(description="Mark selected invoices as PENDING")
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='PENDING')
        self.message_user(request, f"Successfully marked {updated} invoice(s) as PENDING.")


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'unit_price', 'gst_rate', 'line_subtotal', 'tax_amount', 'total_amount')
    list_filter = ('gst_rate', 'created_at')
    search_fields = ('invoice__invoice_number', 'product__name', 'product__sku')
    autocomplete_fields = ('invoice', 'product')
    readonly_fields = ('line_subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at')
