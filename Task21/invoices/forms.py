from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product


class InvoiceForm(forms.ModelForm):
    """
    Form for creating and editing Invoice instances with custom Bootstrap controls.
    """
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
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Net 30'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Invoice notes...'}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)


class InvoiceItemForm(forms.ModelForm):
    """
    Form for individual invoice line item rows within an inline formset.
    """
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
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control unit-price-input', 'step': '0.01'}),
            'gst_rate': forms.NumberInput(attrs={'class': 'form-control gst-input', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control discount-input', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Line item details'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)
