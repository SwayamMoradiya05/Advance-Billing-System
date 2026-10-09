from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product


class CustomerSelectWidget(forms.Select):
    """
    Custom Select widget for Customer selection that attaches rich
    HTML5 data-* attributes to each <option> tag for instant client-side lookup.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value and hasattr(value, 'value'):
            value = value.value

        if value:
            try:
                customer = Customer.objects.get(pk=value)
                option['attrs']['data-phone'] = customer.phone or ''
                option['attrs']['data-email'] = customer.email or ''
                option['attrs']['data-address'] = customer.full_address or ''
                option['attrs']['data-credit-limit'] = str(customer.credit_limit)
                option['attrs']['data-outstanding'] = str(customer.outstanding_balance)
                option['attrs']['data-available-credit'] = str(customer.available_credit)
                option['attrs']['data-tax-id'] = customer.tax_id or 'N/A'
                option['attrs']['data-company'] = customer.company_name or ''
            except Customer.DoesNotExist:
                pass
        return option


class ProductSelectWidget(forms.Select):
    """
    Custom Select widget for Product selection that embeds price, GST rate,
    available stock, and SKU directly inside option attributes.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value and hasattr(value, 'value'):
            value = value.value

        if value:
            try:
                product = Product.objects.get(pk=value)
                option['attrs']['data-price'] = str(product.price)
                option['attrs']['data-gst'] = str(product.gst_rate)
                option['attrs']['data-stock'] = str(product.stock)
                option['attrs']['data-sku'] = product.sku
                option['attrs']['data-hsn'] = product.hsn_code or ''
                option['attrs']['data-unit'] = product.unit or 'pcs'
                option['attrs']['data-description'] = product.description or ''
            except Product.DoesNotExist:
                pass
        return option


class CustomerChoiceField(forms.ModelChoiceField):
    """
    Custom ChoiceField for Customer model with informative dropdown label.
    """
    def label_from_instance(self, obj):
        if obj.company_name:
            return f"{obj.name} ({obj.customer_code}) - {obj.company_name}"
        return f"{obj.name} ({obj.customer_code})"


class ProductChoiceField(forms.ModelChoiceField):
    """
    Custom ChoiceField for Product model with price, stock, and tax detail labels.
    """
    def label_from_instance(self, obj):
        stock_indicator = f"Stock: {obj.stock} {obj.unit}" if obj.stock > 0 else "OUT OF STOCK"
        return f"{obj.name} ({obj.sku}) - ₹{obj.price} [{stock_indicator}, GST: {obj.gst_rate}%]"


class InvoiceForm(forms.ModelForm):
    """
    Form for creating and editing Invoice instances with role-aware customer filtering.
    Restricted to Admin and Distributor operators.
    """
    customer = CustomerChoiceField(
        queryset=Customer.objects.none(),
        widget=CustomerSelectWidget(attrs={'class': 'form-select customer-select'}),
        empty_label="--- Select Customer ---",
        help_text="Choose customer billing account."
    )

    class Meta:
        model = Invoice
        fields = [
            'customer',
            'invoice_date',
            'due_date',
            'status',
            'payment_method',
            'payment_terms',
            'discount_amount',
            'amount_paid',
            'notes',
            'terms_and_conditions',
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Net 30'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control discount-total-input', 'step': '0.01', 'min': '0'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control amount-paid-input', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes or billing remarks...'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamic role-based customer filtering
        active_customers = Customer.objects.filter(is_active=True).order_by('name')
        if user and not (user.is_staff or user.is_superuser) and hasattr(user, 'distributor_profile'):
            # If logged in user is a distributor, prioritize customers managed by this distributor
            distributor_customers = active_customers.filter(distributor=user)
            if distributor_customers.exists():
                self.fields['customer'].queryset = distributor_customers
            else:
                self.fields['customer'].queryset = active_customers
        else:
            self.fields['customer'].queryset = active_customers

    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        discount_amount = cleaned_data.get('discount_amount') or Decimal('0.00')
        amount_paid = cleaned_data.get('amount_paid') or Decimal('0.00')

        if invoice_date and due_date and due_date < invoice_date:
            self.add_error('due_date', 'Payment due date cannot be earlier than invoice date.')

        if discount_amount < Decimal('0.00'):
            self.add_error('discount_amount', 'Overall discount amount cannot be negative.')

        if amount_paid < Decimal('0.00'):
            self.add_error('amount_paid', 'Amount paid cannot be negative.')

        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    """
    Form for individual invoice line items within an inline formset.
    Dynamically loads products with full pricing, GST rate, and stock validation.
    """
    product = ProductChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        widget=ProductSelectWidget(attrs={'class': 'form-select product-select'}),
        empty_label="--- Select Product ---",
        help_text="Select product item to bill."
    )

    class Meta:
        model = InvoiceItem
        fields = [
            'product',
            'quantity',
            'unit_price',
            'gst_rate',
            'discount_percentage',
            'description',
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': 1, 'value': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'step': '0.01', 'placeholder': '0.00'}),
            'gst_rate': forms.NumberInput(attrs={'class': 'form-control gst-input', 'step': '0.01', 'placeholder': '18.00'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control discount-input', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': '0.00'}),
            'description': forms.TextInput(attrs={'class': 'form-control line-desc-input', 'placeholder': 'Line item specifics or serial nos'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        gst_rate = cleaned_data.get('gst_rate')
        discount_percentage = cleaned_data.get('discount_percentage')

        if product:
            # Stock availability check
            if quantity and quantity > product.stock:
                self.add_error(
                    'quantity',
                    f"Insufficient stock for '{product.name}'. Available stock: {product.stock} {product.unit}."
                )

        if quantity is not None and quantity <= 0:
            self.add_error('quantity', 'Quantity must be at least 1.')

        if unit_price is not None and unit_price < Decimal('0.00'):
            self.add_error('unit_price', 'Unit price cannot be negative.')

        if gst_rate is not None and gst_rate < Decimal('0.00'):
            self.add_error('gst_rate', 'GST rate percentage cannot be negative.')

        if discount_percentage is not None:
            if discount_percentage < Decimal('0.00') or discount_percentage > Decimal('100.00'):
                self.add_error('discount_percentage', 'Discount percentage must be between 0% and 100%.')

        return cleaned_data


class BaseInvoiceItemFormSet(BaseInlineFormSet):
    """
    Custom InlineFormSet to validate line item constraints (at least 1 item, no duplicate products).
    """
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        valid_items_count = 0
        seen_products = set()

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue

            product = form.cleaned_data.get('product')
            quantity = form.cleaned_data.get('quantity')

            if product:
                valid_items_count += 1
                if product.pk in seen_products:
                    form.add_error('product', f"Product '{product.name}' is selected multiple times. Please combine quantities into a single row.")
                seen_products.add(product.pk)

        if valid_items_count == 0:
            raise ValidationError("An invoice must contain at least one valid line item.")


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    formset=BaseInvoiceItemFormSet,
    extra=1,
    can_delete=True
)
