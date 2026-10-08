from decimal import Decimal
from products.models import Product


class ProductSerializer:
    """
    Custom JSON serializer and validator helper for Product objects,
    providing lightweight, robust REST API functionality.
    """

    @staticmethod
    def serialize(product):
        """Serialize a Product model instance into a Python dictionary."""
        return {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category,
            'price': str(product.price),
            'stock': product.stock,
            'gst_rate': str(product.gst_rate),
            'gst_amount': str(product.gst_amount),
            'price_with_gst': str(product.price_with_gst),
            'hsn_code': product.hsn_code,
            'unit': product.unit,
            'min_stock_level': product.min_stock_level,
            'description': product.description,
            'is_active': product.is_active,
            'is_low_stock': product.is_low_stock,
            'stock_status': product.stock_status,
            'total_stock_value': str(product.total_stock_value),
            'total_stock_value_with_gst': str(product.total_stock_value_with_gst),
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'updated_at': product.updated_at.isoformat() if product.updated_at else None,
        }

    @staticmethod
    def validate_data(data, instance=None):
        """Validate payload dictionary for creating or updating a product record."""
        errors = {}

        name = str(data.get('name', '')).strip()
        if not name or len(name) < 2:
            errors['name'] = "Product name is required and must be at least 2 characters long."

        if 'price' in data and data['price'] is not None:
            try:
                price = Decimal(str(data['price']))
                if price < Decimal('0.00'):
                    errors['price'] = "Price cannot be negative."
            except Exception:
                errors['price'] = "Invalid numeric value for price."
        else:
            if not instance:
                errors['price'] = "Product price is required."

        if 'stock' in data and data['stock'] is not None:
            try:
                stock = int(data['stock'])
                if stock < 0:
                    errors['stock'] = "Stock quantity cannot be negative."
            except Exception:
                errors['stock'] = "Invalid integer value for stock quantity."

        if 'gst_rate' in data and data['gst_rate'] is not None:
            try:
                gst_rate = Decimal(str(data['gst_rate']))
                if gst_rate < Decimal('0.00'):
                    errors['gst_rate'] = "GST rate percentage cannot be negative."
            except Exception:
                errors['gst_rate'] = "Invalid numeric value for GST rate."

        if 'min_stock_level' in data and data['min_stock_level'] is not None:
            try:
                min_stock = int(data['min_stock_level'])
                if min_stock < 0:
                    errors['min_stock_level'] = "Minimum stock level threshold cannot be negative."
            except Exception:
                errors['min_stock_level'] = "Invalid integer value for minimum stock level."

        sku = str(data.get('sku', '')).strip()
        if sku:
            query = Product.objects.filter(sku__iexact=sku)
            if instance and instance.pk:
                query = query.exclude(pk=instance.pk)
            if query.exists():
                errors['sku'] = "A product with this SKU already exists."

        return errors
