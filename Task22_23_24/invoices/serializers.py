from decimal import Decimal
from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product


class InvoiceItemSerializer:
    """
    Custom JSON serializer / deserializer for InvoiceItem objects.
    """

    @staticmethod
    def serialize(item):
        """Serialize an InvoiceItem instance into a Python dictionary."""
        return {
            'id': item.id,
            'invoice_id': item.invoice.id if item.invoice else None,
            'product_id': item.product.id if item.product else None,
            'product_name': item.product.name if item.product else '',
            'product_sku': item.product.sku if item.product else '',
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'gst_rate': str(item.gst_rate),
            'discount_percentage': str(item.discount_percentage),
            'line_subtotal': str(item.line_subtotal),
            'tax_amount': str(item.tax_amount),
            'total_amount': str(item.total_amount),
            'description': item.description,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None,
        }

    @staticmethod
    def validate_data(data):
        """Validate payload for an invoice line item."""
        errors = {}

        product_id = data.get('product_id') or data.get('product')
        if not product_id:
            errors['product'] = "Product is required for invoice line items."
        else:
            if not Product.objects.filter(pk=product_id).exists():
                errors['product'] = "Selected product does not exist."

        try:
            qty = int(data.get('quantity', 1))
            if qty <= 0:
                errors['quantity'] = "Quantity must be greater than zero."
        except (ValueError, TypeError):
            errors['quantity'] = "Quantity must be a valid integer."

        if 'unit_price' in data and data['unit_price'] is not None:
            try:
                price = Decimal(str(data['unit_price']))
                if price < Decimal('0.00'):
                    errors['unit_price'] = "Unit price cannot be negative."
            except Exception:
                errors['unit_price'] = "Invalid unit price format."

        if 'discount_percentage' in data and data['discount_percentage'] is not None:
            try:
                disc = Decimal(str(data['discount_percentage']))
                if disc < Decimal('0.00') or disc > Decimal('100.00'):
                    errors['discount_percentage'] = "Discount percentage must be between 0% and 100%."
            except Exception:
                errors['discount_percentage'] = "Invalid discount percentage."

        return errors


class InvoiceSerializer:
    """
    Custom JSON serializer / deserializer for Invoice objects.
    """

    @staticmethod
    def serialize(invoice, include_items=True):
        """Serialize an Invoice instance into a Python dictionary."""
        data = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'customer_id': invoice.customer.id if invoice.customer else None,
            'customer_name': invoice.customer.name if invoice.customer else '',
            'customer_code': invoice.customer.customer_code if invoice.customer else '',
            'created_by_id': invoice.created_by.id if invoice.created_by else None,
            'created_by_username': invoice.created_by.username if invoice.created_by else '',
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'status': invoice.status,
            'status_display': invoice.get_status_display(),
            'payment_method': invoice.payment_method,
            'payment_terms': invoice.payment_terms,
            'subtotal': str(invoice.subtotal),
            'tax_amount': str(invoice.tax_amount),
            'discount_amount': str(invoice.discount_amount),
            'grand_total': str(invoice.grand_total),
            'amount_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.balance_due),
            'is_overdue': invoice.is_overdue,
            'total_items_count': invoice.total_items_count,
            'notes': invoice.notes,
            'terms_and_conditions': invoice.terms_and_conditions,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
        }

        if include_items:
            data['items'] = [InvoiceItemSerializer.serialize(item) for item in invoice.items.all()]

        return data

    @staticmethod
    def validate_data(data, instance=None):
        """Validate input dictionary for creating or updating an Invoice."""
        errors = {}

        customer_id = data.get('customer_id') or data.get('customer')
        if not customer_id and not instance:
            errors['customer'] = "Customer is required for creating an invoice."
        elif customer_id:
            if not Customer.objects.filter(pk=customer_id).exists():
                errors['customer'] = "Selected customer does not exist."

        if 'discount_amount' in data and data['discount_amount'] is not None:
            try:
                discount = Decimal(str(data['discount_amount']))
                if discount < Decimal('0.00'):
                    errors['discount_amount'] = "Discount amount cannot be negative."
            except Exception:
                errors['discount_amount'] = "Invalid discount amount format."

        if 'amount_paid' in data and data['amount_paid'] is not None:
            try:
                paid = Decimal(str(data['amount_paid']))
                if paid < Decimal('0.00'):
                    errors['amount_paid'] = "Amount paid cannot be negative."
            except Exception:
                errors['amount_paid'] = "Invalid amount paid format."

        return errors
