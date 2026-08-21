import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Customer
from .forms import CustomerForm, CustomerFilterForm
from .serializers import CustomerSerializer


@login_required
def customer_list_view(request):
    """
    Display a searchable, filterable directory of customers.
    """
    filter_form = CustomerFilterForm(request.GET)
    customers = Customer.objects.all()

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get('q')
        status = filter_form.cleaned_data.get('status')

        if query:
            customers = customers.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(customer_code__icontains=query) |
                Q(company_name__icontains=query)
            )

        if status == 'active':
            customers = customers.filter(is_active=True)
        elif status == 'inactive':
            customers = customers.filter(is_active=False)

    total_count = Customer.objects.count()
    active_count = Customer.objects.filter(is_active=True).count()
    total_outstanding = sum(c.outstanding_balance for c in Customer.objects.filter(is_active=True))

    context = {
        'customers': customers,
        'filter_form': filter_form,
        'total_count': total_count,
        'active_count': active_count,
        'total_outstanding': total_outstanding,
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
def customer_detail_view(request, pk):
    """
    Display detailed profile, contact info, and financial metrics of a customer.
    """
    customer = get_object_or_404(Customer, pk=pk)
    context = {
        'customer': customer,
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
def customer_create_view(request):
    """
    View for adding a new Customer record.
    """
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            if hasattr(request.user, 'distributor_profile'):
                customer.distributor = request.user
            customer.save()
            messages.success(request, f"Customer '{customer.name}' created successfully with Code {customer.customer_code}!")
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, "Please resolve the errors highlighted below.")
    else:
        form = CustomerForm()

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'title': 'Add New Customer',
        'button_text': 'Create Customer Account',
    })


@login_required
def customer_update_view(request, pk):
    """
    View for updating an existing Customer record.
    """
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' updated successfully.")
            return redirect('customer_detail', pk=customer.pk)
        else:
            messages.error(request, "Please correct the highlighted validation errors.")
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Edit Customer: {customer.name}',
        'button_text': 'Save Customer Changes',
    })


@login_required
def customer_delete_view(request, pk):
    """
    View for confirming and deleting a customer.
    """
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f"Customer record for '{name}' was permanently deleted.")
        return redirect('customer_list')

    return render(request, 'customers/customer_confirm_delete.html', {
        'customer': customer,
    })


@login_required
def customer_toggle_status_view(request, pk):
    """
    Quick view to toggle a customer's active/inactive status.
    """
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = not customer.is_active
    customer.save(update_fields=['is_active'])
    status_str = "activated" if customer.is_active else "deactivated"
    messages.info(request, f"Customer '{customer.name}' has been {status_str}.")
    return redirect('customer_detail', pk=customer.pk)


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@csrf_exempt
def api_customer_list_create(request):
    """
    API Endpoint:
    GET  /api/customers/ -> Returns JSON list of customers
    POST /api/customers/ -> Creates a new customer
    """
    if request.method == 'GET':
        customers = Customer.objects.all()
        query = request.GET.get('q')
        if query:
            customers = customers.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(customer_code__icontains=query)
            )

        data = [CustomerSerializer.serialize(c) for c in customers]
        return JsonResponse({'status': 'success', 'count': len(data), 'customers': data}, status=200)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'status': 'error', 'error': 'Invalid JSON body in payload.'}, status=400)

        errors = CustomerSerializer.validate_data(body)
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        customer = Customer(
            name=body['name'].strip(),
            email=body['email'].strip().lower(),
            phone=body['phone'].strip(),
            company_name=body.get('company_name', '').strip() or None,
            address=body['address'].strip(),
            city=body.get('city', '').strip(),
            state=body.get('state', '').strip(),
            postal_code=body.get('postal_code', '').strip(),
            country=body.get('country', 'India').strip(),
            tax_id=body.get('tax_id', '').strip() or None,
            credit_limit=Decimal(str(body.get('credit_limit', '10000.00'))),
            outstanding_balance=Decimal(str(body.get('outstanding_balance', '0.00'))),
            is_active=bool(body.get('is_active', True)),
            notes=body.get('notes', '').strip(),
        )
        customer.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Customer created successfully via API.',
            'customer': CustomerSerializer.serialize(customer)
        }, status=201)

    return HttpResponseNotAllowed(['GET', 'POST'])


@csrf_exempt
def api_customer_detail(request, pk):
    """
    API Endpoint:
    GET    /api/customers/<pk>/ -> Fetch customer details
    PUT    /api/customers/<pk>/ -> Update customer details
    DELETE /api/customers/<pk>/ -> Delete customer record
    """
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': f'Customer with ID {pk} not found.'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'customer': CustomerSerializer.serialize(customer)
        }, status=200)

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'status': 'error', 'error': 'Invalid JSON body payload.'}, status=400)

        errors = CustomerSerializer.validate_data(body, instance=customer)
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        customer.name = body['name'].strip()
        customer.email = body['email'].strip().lower()
        customer.phone = body['phone'].strip()
        customer.company_name = body.get('company_name', '').strip() or None
        customer.address = body['address'].strip()
        if 'city' in body: customer.city = body['city'].strip()
        if 'state' in body: customer.state = body['state'].strip()
        if 'postal_code' in body: customer.postal_code = body['postal_code'].strip()
        if 'country' in body: customer.country = body['country'].strip()
        if 'tax_id' in body: customer.tax_id = body['tax_id'].strip() or None
        if 'credit_limit' in body: customer.credit_limit = Decimal(str(body['credit_limit']))
        if 'outstanding_balance' in body: customer.outstanding_balance = Decimal(str(body['outstanding_balance']))
        if 'is_active' in body: customer.is_active = bool(body['is_active'])
        if 'notes' in body: customer.notes = body['notes'].strip()
        customer.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Customer updated successfully via API.',
            'customer': CustomerSerializer.serialize(customer)
        }, status=200)

    elif request.method == 'DELETE':
        code = customer.customer_code
        customer.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Customer {code} deleted successfully via API.'
        }, status=200)

    return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE'])
