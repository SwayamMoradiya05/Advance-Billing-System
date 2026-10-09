import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product
from .forms import ProductForm, ProductSearchFilterForm
from .serializers import ProductSerializer


def product_list_view(request):
    """
    Display searchable, filterable catalog of Products with metrics and pagination.
    """
    filter_form = ProductSearchFilterForm(request.GET)
    products_qs = Product.objects.all()

    query = ''
    category = ''
    stock_status = ''
    sort_by = '-created_at'

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get('q') or ''
        category = filter_form.cleaned_data.get('category') or ''
        stock_status = filter_form.cleaned_data.get('stock_status') or ''
        sort_by = filter_form.cleaned_data.get('sort_by') or '-created_at'

    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query) |
            Q(hsn_code__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        products_qs = products_qs.filter(category=category)

    if stock_status == 'in_stock':
        products_qs = products_qs.filter(stock__gt=0)
    elif stock_status == 'low_stock':
        # Filter products where stock > 0 and stock <= min_stock_level
        products_qs = [p for p in products_qs if p.is_low_stock and p.stock > 0]
        p_ids = [p.id for p in products_qs]
        products_qs = Product.objects.filter(id__in=p_ids)
    elif stock_status == 'out_of_stock':
        products_qs = products_qs.filter(stock__lte=0)

    # Sorting
    valid_sorts = ['-created_at', 'name', '-name', 'price', '-price', 'stock', '-stock']
    if isinstance(products_qs, list):
        # Already evaluated list from custom property filter
        if sort_by in valid_sorts:
            reverse = sort_by.startswith('-')
            attr = sort_by.lstrip('-')
            products_qs.sort(key=lambda p: getattr(p, attr, 0), reverse=reverse)
    else:
        if sort_by in valid_sorts:
            products_qs = products_qs.order_by(sort_by)
        else:
            products_qs = products_qs.order_by('-created_at')

    # Overall system metrics
    all_products = Product.objects.all()
    total_count = all_products.count()
    active_count = all_products.filter(is_active=True).count()
    low_stock_count = sum(1 for p in all_products if p.is_low_stock)
    out_of_stock_count = all_products.filter(stock__lte=0).count()
    total_valuation = sum(p.total_stock_value for p in all_products)
    total_valuation_with_gst = sum(p.total_stock_value_with_gst for p in all_products)

    filtered_count = len(products_qs) if isinstance(products_qs, list) else products_qs.count()

    # Pagination: 10 products per page
    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get('page', 1)
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Preserve GET params for pagination
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    encoded_query = query_params.urlencode()

    context = {
        'products': products,
        'filter_form': filter_form,
        'total_count': total_count,
        'active_count': active_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_valuation': total_valuation,
        'total_valuation_with_gst': total_valuation_with_gst,
        'filtered_count': filtered_count,
        'query': query,
        'category': category,
        'stock_status': stock_status,
        'sort_by': sort_by,
        'encoded_query': encoded_query,
    }
    return render(request, 'products/product_list.html', context)


def product_detail_view(request, pk):
    """
    Display detailed specification, pricing, GST calculation, and stock breakdown for a product.
    """
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
    }
    return render(request, 'products/product_detail.html', context)


def product_create_view(request):
    """
    View for creating a new Product record.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(
                request,
                f"Product '{product.name}' created successfully with SKU {product.sku}!"
            )
            return redirect('product_detail', pk=product.pk)
        else:
            messages.error(request, "Please correct the errors highlighted in the form below.")
    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'button_text': 'Create Product',
    })


def product_update_view(request, pk):
    """
    View for editing an existing Product record.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('product_detail', pk=product.pk)
        else:
            messages.error(request, "Please correct the highlighted validation errors.")
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'button_text': 'Save Product Changes',
    })


def product_delete_view(request, pk):
    """
    View for confirming and deleting a Product record.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        name = product.name
        sku = product.sku
        product.delete()
        messages.success(request, f"Product '{name}' ({sku}) was deleted successfully.")
        return redirect('product_list')

    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
    })


def product_toggle_status_view(request, pk):
    """
    Toggle active/inactive status of a product.
    """
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    status_str = "activated" if product.is_active else "deactivated"
    messages.info(request, f"Product '{product.name}' has been {status_str}.")
    return redirect('product_detail', pk=product.pk)


# =============================================================================
# REST API ENDPOINTS
# =============================================================================

@csrf_exempt
def api_product_list_create(request):
    """
    REST API Endpoint:
    GET  /products/api/products/ -> JSON list of products with optional search/filter
    POST /products/api/products/ -> Create a product via JSON payload
    """
    if request.method == 'GET':
        products = Product.objects.all()
        query = request.GET.get('q')
        category = request.GET.get('category')
        stock_status = request.GET.get('stock_status')

        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(category__icontains=query) |
                Q(hsn_code__icontains=query)
            )

        if category:
            products = products.filter(category=category)

        if stock_status == 'in_stock':
            products = products.filter(stock__gt=0)
        elif stock_status == 'out_of_stock':
            products = products.filter(stock__lte=0)

        data = [ProductSerializer.serialize(p) for p in products]
        return JsonResponse({'status': 'success', 'count': len(data), 'products': data}, status=200)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'status': 'error', 'error': 'Invalid JSON body payload.'}, status=400)

        errors = ProductSerializer.validate_data(body)
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        product = Product(
            name=body['name'].strip(),
            category=body.get('category', 'General').strip(),
            price=Decimal(str(body.get('price', '0.00'))),
            stock=int(body.get('stock', 0)),
            gst_rate=Decimal(str(body.get('gst_rate', '18.00'))),
            hsn_code=body.get('hsn_code', '').strip(),
            unit=body.get('unit', 'pcs').strip(),
            min_stock_level=int(body.get('min_stock_level', 10)),
            description=body.get('description', '').strip(),
            is_active=bool(body.get('is_active', True)),
        )

        sku = body.get('sku', '').strip()
        if sku:
            product.sku = sku

        product.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Product created successfully via API.',
            'product': ProductSerializer.serialize(product)
        }, status=201)

    return HttpResponseNotAllowed(['GET', 'POST'])


@csrf_exempt
def api_product_detail(request, pk):
    """
    REST API Endpoint:
    GET    /products/api/products/<pk>/ -> Fetch single product JSON
    PUT    /products/api/products/<pk>/ -> Update product JSON
    DELETE /products/api/products/<pk>/ -> Delete product
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': f'Product with ID {pk} not found.'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'product': ProductSerializer.serialize(product)
        }, status=200)

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'status': 'error', 'error': 'Invalid JSON body payload.'}, status=400)

        errors = ProductSerializer.validate_data(body, instance=product)
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        if 'name' in body: product.name = body['name'].strip()
        if 'category' in body: product.category = body['category'].strip()
        if 'price' in body: product.price = Decimal(str(body['price']))
        if 'stock' in body: product.stock = int(body['stock'])
        if 'gst_rate' in body: product.gst_rate = Decimal(str(body['gst_rate']))
        if 'hsn_code' in body: product.hsn_code = body['hsn_code'].strip()
        if 'unit' in body: product.unit = body['unit'].strip()
        if 'min_stock_level' in body: product.min_stock_level = int(body['min_stock_level'])
        if 'description' in body: product.description = body['description'].strip()
        if 'is_active' in body: product.is_active = bool(body['is_active'])
        if 'sku' in body and body['sku'].strip(): product.sku = body['sku'].strip()

        product.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Product updated successfully via API.',
            'product': ProductSerializer.serialize(product)
        }, status=200)

    elif request.method == 'DELETE':
        sku = product.sku
        product.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Product {sku} deleted successfully via API.'
        }, status=200)

    return HttpResponseNotAllowed(['GET', 'PUT', 'DELETE'])
