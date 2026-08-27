import base64
import os
import json
from io import BytesIO
import qrcode
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from .serializers import InvoiceSerializer, InvoiceItemSerializer
from .utils import render_to_pdf
from customers.models import Customer
from products.models import Product


def is_admin_or_distributor(user):
    """
    Check if the authenticated user has permission to create and manage invoices.
    Permitted roles: System Administrators (is_staff / is_superuser) and Distributors (distributor_profile).
    """
    if not user.is_authenticated:
        return False
    return user.is_staff or user.is_superuser or hasattr(user, 'distributor_profile')


def admin_or_distributor_required(view_func):
    """
    Decorator to restrict view access exclusively to Admins and Distributors.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_or_distributor(request.user):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'api/' in request.path:
                return JsonResponse({
                    'success': False,
                    'error': 'Access Denied: Invoice creation and management is restricted to Admin and Distributor accounts only.'
                }, status=403)
            messages.error(
                request,
                'Access Denied: Invoice creation is restricted to Admin and Distributor accounts only.'
            )
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
def invoice_list_view(request):
    """
    Display a searchable, filterable invoice listing with pagination and aggregate metrics.
    """
    invoices_qs = Invoice.objects.select_related('customer', 'created_by').all()

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort = request.GET.get('sort', '-created_at')

    if query:
        invoices_qs = invoices_qs.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__customer_code__icontains=query) |
            Q(customer__email__icontains=query)
        )

    if status_filter:
        invoices_qs = invoices_qs.filter(status=status_filter)

    valid_sorts = ['-created_at', 'created_at', '-grand_total', 'grand_total', '-invoice_date', 'due_date']
    if sort in valid_sorts:
        invoices_qs = invoices_qs.order_by(sort)
    else:
        invoices_qs = invoices_qs.order_by('-created_at')

    # Aggregates
    total_count = Invoice.objects.count()
    paid_count = Invoice.objects.filter(status='PAID').count()
    pending_count = Invoice.objects.filter(status='PENDING').count()
    total_revenue = Invoice.objects.filter(status='PAID').aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')

    paginator = Paginator(invoices_qs, 10)
    page = request.GET.get('page', 1)
    try:
        invoices = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        invoices = paginator.page(1)

    can_create = is_admin_or_distributor(request.user)

    context = {
        'invoices': invoices,
        'query': query,
        'status_filter': status_filter,
        'sort': sort,
        'total_count': total_count,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'status_choices': Invoice.STATUS_CHOICES,
        'can_create': can_create,
    }
    return render(request, 'invoices/invoice_list.html', context)


@login_required
def invoice_detail_view(request, pk):
    """
    Display complete details of a specific Invoice including line items.
    """
    invoice = get_object_or_404(Invoice.objects.select_related('customer', 'created_by').prefetch_related('items__product'), pk=pk)
    context = {
        'invoice': invoice,
        'items': invoice.items.all(),
    }
    return render(request, 'invoices/invoice_detail.html', context)


@login_required
def invoice_pdf_view(request, pk):
    """
    Generate and stream downloadable PDF document for a specific Invoice with logo and company branding.
    """
    invoice = get_object_or_404(Invoice.objects.select_related('customer', 'created_by').prefetch_related('items__product'), pk=pk)

    # Encode logo image into Base64 string for standalone PDF embedding
    logo_base64 = None
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'company_logo.jpg')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as img_file:
                logo_base64 = f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
        except Exception:
            logo_base64 = None

    company_info = {
        'name': 'Advance Billing System Pvt. Ltd.',
        'tagline': 'Enterprise Wholesale & Logistics Solutions',
        'gstin': '24AAACA0000A1Z5',
        'address': 'Suite 502, Industrial Trade Center, Sector 11',
        'city_state': 'Ahmedabad, Gujarat - 380015',
        'phone': '+91 98765 43210',
        'email': 'billing@advancebilling.com',
        'website': 'www.advancebilling.com',
        'bank_name': 'HDFC Bank Ltd.',
        'bank_account': '50200012345678',
        'bank_ifsc': 'HDFC0000123',
        'upi_id': 'advancebilling@hdfcbank'
    }

    # Generate Dynamic Verification QR Code
    qr_base64 = None
    try:
        qr_payload = json.dumps({
            'invoice': invoice.invoice_number,
            'customer': invoice.customer.name if invoice.customer else 'N/A',
            'date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
            'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
            'items_count': invoice.total_items_count,
            'subtotal': str(invoice.subtotal),
            'tax': str(invoice.tax_amount),
            'total': str(invoice.grand_total),
            'status': invoice.status,
            'verified': True,
            'hash': f"VERIFIED-INTAKE-{invoice.pk}-{invoice.invoice_number}"
        })
        qr_img = qrcode.make(qr_payload)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_base64 = f"data:image/png;base64,{base64.b64encode(qr_buffer.getvalue()).decode('utf-8')}"
    except Exception:
        qr_base64 = None

    context = {
        'invoice': invoice,
        'items': invoice.items.all(),
        'logo_base64': logo_base64,
        'qr_base64': qr_base64,
        'company': company_info,
    }
    pdf_content = render_to_pdf('invoices/invoice_pdf.html', context)
    if pdf_content:
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    messages.error(request, "Failed to generate PDF document. Please try again.")
    return redirect('invoice_detail', pk=invoice.pk)


@login_required
@admin_or_distributor_required
def invoice_create_view(request):
    """
    Create a new Invoice with attached InvoiceItems using formsets.
    Restricted to Admin and Distributor accounts.
    """
    if request.method == 'POST':
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()

            formset.instance = invoice
            formset.save()

            # Recalculate totals from saved line items
            invoice.calculate_totals(save_instance=True)

            messages.success(request, f"Invoice #{invoice.invoice_number} generated successfully for {invoice.customer.name}!")
            return redirect('invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Please resolve the form validation errors highlighted below.")
    else:
        form = InvoiceForm(user=request.user)
        formset = InvoiceItemFormSet()

    is_admin = request.user.is_staff or request.user.is_superuser
    is_distributor = hasattr(request.user, 'distributor_profile')
    user_role = "System Administrator" if is_admin else ("Registered Distributor" if is_distributor else "Operator")

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Customer Invoice',
        'user_role': user_role,
        'is_admin': is_admin,
        'is_distributor': is_distributor,
    }
    return render(request, 'invoices/invoice_form.html', context)


# -----------------------------------------------------------------------------
# Dynamic REST API Endpoints for Dropdowns & Operations
# -----------------------------------------------------------------------------

@login_required
def api_customer_detail(request, pk):
    """
    Dynamic JSON lookup for a specific Customer by Primary Key.
    Used by front-end JS to render real-time customer cards and credit limits.
    """
    customer = get_object_or_404(Customer, pk=pk)
    return JsonResponse({
        'success': True,
        'customer': {
            'id': customer.id,
            'customer_code': customer.customer_code,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'company_name': customer.company_name or '',
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'postal_code': customer.postal_code,
            'full_address': customer.full_address,
            'tax_id': customer.tax_id or 'N/A',
            'credit_limit': str(customer.credit_limit),
            'outstanding_balance': str(customer.outstanding_balance),
            'available_credit': str(customer.available_credit),
            'has_available_credit': customer.has_available_credit,
        }
    })


@login_required
def api_product_detail(request, pk):
    """
    Dynamic JSON lookup for a specific Product by Primary Key.
    Used by front-end JS when selecting a product from line item dropdowns.
    """
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'category': product.category,
            'price': str(product.price),
            'stock': product.stock,
            'gst_rate': str(product.gst_rate),
            'hsn_code': product.hsn_code,
            'unit': product.unit,
            'description': product.description,
            'is_low_stock': product.is_low_stock,
            'stock_status': product.stock_status,
        }
    })


def api_invoice_list(request):
    """
    JSON REST API endpoint for retrieving and creating invoices.
    Invoice creation via API is restricted to Admins and Distributors.
    """
    if request.method == 'GET':
        invoices = Invoice.objects.select_related('customer', 'created_by').prefetch_related('items__product').all()
        
        customer_id = request.GET.get('customer')
        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
            
        status = request.GET.get('status')
        if status:
            invoices = invoices.filter(status=status)

        serialized = [InvoiceSerializer.serialize(inv) for inv in invoices]
        return JsonResponse({'success': True, 'count': len(serialized), 'invoices': serialized})

    elif request.method == 'POST':
        if not is_admin_or_distributor(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Access Denied: Invoice creation is restricted to Admin and Distributor accounts only.'
            }, status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': {'detail': 'Invalid JSON format.'}}, status=400)

        errors = InvoiceSerializer.validate_data(payload)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        customer = get_object_or_404(Customer, pk=payload.get('customer_id') or payload.get('customer'))
        
        invoice = Invoice(
            customer=customer,
            status=payload.get('status', 'DRAFT'),
            payment_method=payload.get('payment_method', 'CASH'),
            payment_terms=payload.get('payment_terms', 'Net 30'),
            discount_amount=Decimal(str(payload.get('discount_amount', 0))),
            amount_paid=Decimal(str(payload.get('amount_paid', 0))),
            notes=payload.get('notes', ''),
            terms_and_conditions=payload.get('terms_and_conditions', 'Thank you for your business!'),
        )
        if request.user.is_authenticated:
            invoice.created_by = request.user
        invoice.save()

        # Handle items if provided
        items_payload = payload.get('items', [])
        for item_data in items_payload:
            product_id = item_data.get('product_id') or item_data.get('product')
            if product_id and Product.objects.filter(pk=product_id).exists():
                prod = Product.objects.get(pk=product_id)
                item = InvoiceItem(
                    invoice=invoice,
                    product=prod,
                    quantity=int(item_data.get('quantity', 1)),
                    unit_price=Decimal(str(item_data.get('unit_price', prod.price))),
                    gst_rate=Decimal(str(item_data.get('gst_rate', prod.gst_rate))),
                    discount_percentage=Decimal(str(item_data.get('discount_percentage', 0))),
                    description=item_data.get('description', ''),
                )
                item.save()

        invoice.calculate_totals(save_instance=True)
        return JsonResponse({'success': True, 'invoice': InvoiceSerializer.serialize(invoice)}, status=201)

    return HttpResponseNotAllowed(['GET', 'POST'])


def api_invoice_detail(request, pk):
    """
    JSON REST API endpoint for retrieving a single invoice.
    """
    invoice = get_object_or_404(Invoice.objects.select_related('customer', 'created_by').prefetch_related('items__product'), pk=pk)
    if request.method == 'GET':
        return JsonResponse({'success': True, 'invoice': InvoiceSerializer.serialize(invoice)})
    return HttpResponseNotAllowed(['GET'])
