from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    """
    Form for creating and updating Product records with Bootstrap 5 styling.
    """
    class Meta:
        model = Product
        fields = [
            'sku',
            'name',
            'category',
            'price',
            'stock',
            'gst_rate',
            'hsn_code',
            'unit',
            'min_stock_level',
            'description',
            'is_active',
        ]
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Auto-generated if left blank (e.g. PRD-1001)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'Enter product name / title'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'min': '0',
                'placeholder': '0'
            }),
            'gst_rate': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'hsn_code': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'placeholder': 'e.g., 84713010'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'min': '0',
                'placeholder': '10'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'rows': 3,
                'placeholder': 'Product description or technical notes...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sku'].required = False  # SKU can be auto-generated


class ProductSearchFilterForm(forms.Form):
    """
    Form for filtering and searching the Product catalog in the UI.
    """
    STOCK_STATUS_CHOICES = [
        ('', 'All Stock Statuses'),
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]

    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('name', 'Name (A-Z)'),
        ('-name', 'Name (Z-A)'),
        ('price', 'Price (Low to High)'),
        ('-price', 'Price (High to Low)'),
        ('stock', 'Stock (Low to High)'),
        ('-stock', 'Stock (High to Low)'),
    ]

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark text-white border-secondary',
            'placeholder': 'Search by Name, SKU, HSN Code, or Category...'
        })
    )
    category = forms.CharField(
        required=False,
        widget=forms.Select(
            choices=[('', 'All Categories')] + Product.CATEGORY_CHOICES,
            attrs={'class': 'form-select bg-dark text-white border-secondary'}
        )
    )
    stock_status = forms.ChoiceField(
        choices=STOCK_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'})
    )
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'})
    )
