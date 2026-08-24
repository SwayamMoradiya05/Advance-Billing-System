import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from .serializers import InvoiceSerializer, InvoiceItemSerializer
from customers.models import Customer
from products.models import Product


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
def invoice_create_view(request):
    """
    Create a new Invoice with attached InvoiceItems using formsets.
    """
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()

            formset.instance = invoice
            formset.save()

            # Recalculate totals
            invoice.calculate_totals(save_instance=True)

            messages.success(request, f"Invoice {invoice.invoice_number} created successfully!")
            return redirect('invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Invoice',
    }
    return render(request, 'invoices/invoice_form.html', context)


# -----------------------------------------------------------------------------
# REST API JSON Endpoints
# -----------------------------------------------------------------------------

def api_invoice_list(request):
    """
    JSON REST API endpoint for retrieving and creating invoices.
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
