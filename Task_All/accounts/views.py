import json

import random



from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout, get_user_model

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.http import JsonResponse

from django.views.decorators.http import require_http_methods

from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q, Sum, Count

from django.core.mail import send_mail

from django.conf import settings



from .forms import (

    LoginForm,

    DistributorLoginForm,

    DistributorRegistrationForm,

    DistributorProfileForm

)

from .models import OTPCode, DistributorProfile

from .serializers import AdminRegistrationSerializer

from products.models import Product

from customers.models import Customer

from invoices.models import Invoice, InvoiceItem

from datetime import timedelta, date

from decimal import Decimal



from django.db import models

from django.utils import timezone





User = get_user_model()





def login_view(request):

    """Admin Governance Sign In View"""



    if request.user.is_authenticated:

        return redirect('dashboard')



    if request.method == 'POST':

        form = LoginForm(request.POST)



        if form.is_valid():

            user = form.cleaned_data['user']

            login(request, user)



            if not form.cleaned_data.get('remember_me'):

                request.session.set_expiry(0)



            next_url = request.GET.get('next') or 'dashboard'

            return redirect(next_url)



    else:

        form = LoginForm()



    return render(request, 'accounts/login.html', {'form': form})





def distributor_login_view(request):

    """Distributor Logistics Portal Sign In View"""



    if request.user.is_authenticated:



        if request.user.is_staff or request.user.is_superuser:

            return redirect('dashboard')



        return redirect('distributor_dashboard')



    if request.method == 'POST':



        form = DistributorLoginForm(request.POST)



        if form.is_valid():



            user = form.cleaned_data['user']



            login(request, user)



            if not form.cleaned_data.get('remember_me'):

                request.session.set_expiry(0)



            next_url = request.GET.get('next')



            if not next_url:



                if user.is_staff or user.is_superuser:

                    next_url = 'dashboard'

                else:

                    next_url = 'distributor_dashboard'



            return redirect(next_url)



    else:

        form = DistributorLoginForm()



    return render(

        request,

        'accounts/distributor_login.html',

        {'form': form}

    )





def distributor_register_view(request):

    """Distributor Registration View"""



    if request.user.is_authenticated:

        return redirect('dashboard')



    if request.method == 'POST':



        form = DistributorRegistrationForm(request.POST)



        if form.is_valid():



            full_name = form.cleaned_data['full_name']

            email = form.cleaned_data['email']

            phone = form.cleaned_data['phone']

            company_name = form.cleaned_data.get('company_name', '')

            password = form.cleaned_data['password']



            username = email.split('@')[0] + f"{random.randint(100, 999)}"



            name_parts = full_name.strip().split(' ', 1)



            first_name = name_parts[0]

            last_name = name_parts[1] if len(name_parts) > 1 else ''



            user = User.objects.create_user(

                username=username,

                email=email,

                password=password,

                first_name=first_name,

                last_name=last_name

            )



            distributor_id = f"DIST-{random.randint(1000, 9999)}"



            DistributorProfile.objects.create(

                user=user,

                phone=phone,

                company_name=company_name or f"{first_name} Logistics",

                distributor_id=distributor_id

            )



            messages.success(

                request,

                f"Distributor account created successfully! Welcome, {first_name}. Please sign in."

            )



            return redirect('distributor_login')



        else:

            messages.error(

                request,

                "Please resolve the validation errors below."

            )



    else:

        form = DistributorRegistrationForm()



    return render(

        request,

        'accounts/distributor_register.html',

        {'form': form}

    )





@csrf_exempt

@require_http_methods(["POST"])

def api_register_view(request):

    """API endpoint for Distributor Registration"""



    try:

        data = json.loads(request.body)



    except (json.JSONDecodeError, TypeError):

        data = request.POST



    form = DistributorRegistrationForm(data)



    if form.is_valid():



        full_name = form.cleaned_data['full_name']

        email = form.cleaned_data['email']

        phone = form.cleaned_data['phone']

        company_name = form.cleaned_data.get('company_name', '')

        password = form.cleaned_data['password']



        username = email.split('@')[0] + f"{random.randint(100, 999)}"



        name_parts = full_name.strip().split(' ', 1)



        first_name = name_parts[0]

        last_name = name_parts[1] if len(name_parts) > 1 else ''



        user = User.objects.create_user(

            username=username,

            email=email,

            password=password,

            first_name=first_name,

            last_name=last_name

        )



        distributor_id = f"DIST-{random.randint(1000, 9999)}"



        DistributorProfile.objects.create(

            user=user,

            phone=phone,

            company_name=company_name or f"{first_name} Logistics",

            distributor_id=distributor_id

        )



        return JsonResponse(

            {

                'message': (

                    f"Distributor account created successfully! "

                    f"Welcome, {first_name}. Please sign in."

                ),

                'distributor_id': distributor_id,

                'redirect_url': '/distributor-login/'

            },

            status=201

        )



    else:



        errors = {

            field: [str(e) for e in err_list]

            for field, err_list in form.errors.items()

        }



        return JsonResponse(

            {

                'error': 'Validation failed',

                'details': errors

            },

            status=400

        )





@csrf_exempt

@require_http_methods(["POST"])

def api_admin_register_view(request):

    """API endpoint for Admin / Staff User Registration"""



    try:

        data = json.loads(request.body)



    except (json.JSONDecodeError, TypeError):

        data = request.POST



    serializer = AdminRegistrationSerializer(data)



    if serializer.is_valid():



        cdata = serializer.cleaned_data



        user = User.objects.create_user(

            username=cdata['username'],

            email=cdata['email'],

            password=cdata['password'],

            first_name=cdata['first_name'],

            last_name=cdata['last_name']

        )



        user.is_staff = True



        if cdata['is_superuser']:

            user.is_superuser = True



        user.save()



        return JsonResponse(

            {

                'status': 'success',

                'message': 'Admin account created successfully.',

                'user': {

                    'id': user.id,

                    'username': user.username,

                    'email': user.email,

                    'first_name': user.first_name,

                    'last_name': user.last_name,

                    'is_staff': user.is_staff,

                    'is_superuser': user.is_superuser,

                }

            },

            status=201

        )



    else:



        return JsonResponse(

            {

                'status': 'error',

                'error': 'Validation failed',

                'details': serializer.errors

            },

            status=400

        )





@csrf_exempt

@require_http_methods(["POST"])

def api_login_view(request):



    try:

        data = json.loads(request.body)



    except (json.JSONDecodeError, TypeError):



        return JsonResponse(

            {'error': 'Invalid JSON body'},

            status=400

        )



    username = data.get('username')

    password = data.get('password')



    if not username or not password:



        return JsonResponse(

            {'error': 'Username and password are required'},

            status=400

        )



    user = authenticate(

        request,

        username=username,

        password=password

    )



    if user is None:



        try:



            user_obj = User.objects.get(

                username=username

            )



            if user_obj.check_password(password) and not user_obj.is_active:



                return JsonResponse(

                    {'error': 'Account is disabled'},

                    status=403

                )



        except User.DoesNotExist:

            pass



        return JsonResponse(

            {'error': 'Invalid credentials'},

            status=401

        )



    login(request, user)



    return JsonResponse(

        {

            'message': 'Login successful',

            'user': {

                'id': user.id,

                'username': user.username,

                'name': user.first_name or user.username,

                'email': user.email,

            }

        },

        status=200

    )





# ============================================================

# ADMIN PASSWORD RECOVERY - REQUEST OTP

# ============================================================



@csrf_exempt

@require_http_methods(["POST"])

def api_request_otp_view(request):

    """

    Request an OTP for Admin password recovery.



    Only staff/superuser accounts are allowed.

    OTP is sent to the registered admin email address.

    """



    try:

        data = json.loads(request.body)



    except (json.JSONDecodeError, TypeError):

        data = request.POST



    raw_input = data.get('email') or data.get('username')



    if not raw_input:



        return JsonResponse(

            {

                'error': 'Admin email or username is required.'

            },

            status=400

        )



    clean_input = str(raw_input).strip()



    # --------------------------------------------------------

    # Find Admin by username or email

    # --------------------------------------------------------



    admin_user = User.objects.filter(

        Q(email__iexact=clean_input) |

        Q(username__iexact=clean_input),

        is_staff=True

    ).first()



    # Also allow superusers even if is_staff was not explicitly set

    if admin_user is None:



        admin_user = User.objects.filter(

            Q(email__iexact=clean_input) |

            Q(username__iexact=clean_input),

            is_superuser=True

        ).first()



    # --------------------------------------------------------

    # Admin account validation

    # --------------------------------------------------------



    if admin_user is None:



        return JsonResponse(

            {

                'error': 'No administrator account was found with these details.'

            },

            status=404

        )



    if not admin_user.is_active:



        return JsonResponse(

            {

                'error': 'This administrator account is inactive.'

            },

            status=403

        )



    if not admin_user.email:



        return JsonResponse(

            {

                'error': 'This administrator account does not have a registered email address.'

            },

            status=400

        )



    target_email = admin_user.email.strip().lower()



    # --------------------------------------------------------

    # Generate OTP

    # --------------------------------------------------------



    otp = OTPCode.generate_otp(target_email)



    # --------------------------------------------------------

    # Send OTP to registered Admin email

    # --------------------------------------------------------



    try:



        send_mail(

            subject='Admin Password Recovery OTP - Advance Billing System',



            message=(

                f'Hello {admin_user.get_full_name() or admin_user.username},\n\n'

                f'Your password recovery OTP is: {otp.code}\n\n'

                f'This OTP is valid for 10 minutes and can only be used once.\n\n'

                f'If you did not request a password reset, please ignore this email.\n\n'

                f'Advance Billing System'

            ),



            from_email=getattr(

                settings,

                'DEFAULT_FROM_EMAIL',

                settings.EMAIL_HOST_USER

            ),



            recipient_list=[target_email],



            fail_silently=False,

        )



    except Exception as e:



        # Invalidate OTP if email sending failed

        otp.is_used = True

        otp.save(update_fields=['is_used'])



        print(f"Admin Password Recovery Email Error: {e}")



        return JsonResponse(

            {

                'error': 'Unable to send the recovery email. Please try again later.'

            },

            status=500

        )



    # IMPORTANT:

    # OTP is deliberately NOT returned in this response.



    return JsonResponse(

        {

            'message': 'Password recovery OTP has been sent to your registered admin email.',

            'email': target_email,

            'email_sent': True

        },

        status=200

    )





# ============================================================

# ADMIN PASSWORD RECOVERY - VERIFY OTP + RESET PASSWORD

# ============================================================



@csrf_exempt

@require_http_methods(["POST"])

def api_verify_otp_view(request):

    """

    Verify Admin OTP and reset Admin password.



    Password is changed only when:

    - Admin account exists

    - OTP is valid

    - OTP is not expired

    - OTP has not already been used

    - New password satisfies Django password validation

    """



    try:

        data = json.loads(request.body)



    except (json.JSONDecodeError, TypeError):

        data = request.POST



    email_or_username = data.get('email') or data.get('username')

    code = data.get('code') or data.get('otp')

    new_password = data.get('new_password')



    if not email_or_username:



        return JsonResponse(

            {

                'error': 'Admin email or username is required.'

            },

            status=400

        )



    if not code:



        return JsonResponse(

            {

                'error': 'OTP code is required.'

            },

            status=400

        )



    if not new_password:



        return JsonResponse(

            {

                'error': 'New password is required.'

            },

            status=400

        )



    clean_input = str(email_or_username).strip()



    # --------------------------------------------------------

    # Find Admin account

    # --------------------------------------------------------



    admin_user = User.objects.filter(

        Q(email__iexact=clean_input) |

        Q(username__iexact=clean_input),

        is_staff=True

    ).first()



    if admin_user is None:



        admin_user = User.objects.filter(

            Q(email__iexact=clean_input) |

            Q(username__iexact=clean_input),

            is_superuser=True

        ).first()



    if admin_user is None:



        return JsonResponse(

            {

                'error': 'Administrator account not found.'

            },

            status=404

        )



    if not admin_user.is_active:



        return JsonResponse(

            {

                'error': 'This administrator account is inactive.'

            },

            status=403

        )



    if not admin_user.email:



        return JsonResponse(

            {

                'error': 'Administrator email address is not configured.'

            },

            status=400

        )



    target_email = admin_user.email.strip().lower()



    # --------------------------------------------------------

    # Validate OTP against the registered admin email

    # --------------------------------------------------------



    otp_valid = OTPCode.validate_otp(

        target_email,

        str(code).strip()

    )



    if not otp_valid:



        return JsonResponse(

            {

                'error': 'Invalid or expired OTP.'

            },

            status=400

        )



    # --------------------------------------------------------

    # Validate new password using Django validators

    # --------------------------------------------------------



    from django.contrib.auth.password_validation import validate_password

    from django.core.exceptions import ValidationError



    try:



        validate_password(

            new_password,

            user=admin_user

        )



    except ValidationError as e:



        return JsonResponse(

            {

                'error': 'Password validation failed.',

                'details': e.messages

            },

            status=400

        )



    # --------------------------------------------------------

    # Set new password securely

    # --------------------------------------------------------



    admin_user.set_password(new_password)

    admin_user.save(update_fields=['password'])



    return JsonResponse(

        {

            'message': 'Administrator password has been reset successfully.'

        },

        status=200

    )





def logout_view(request):



    logout(request)



    if (

        request.headers.get('x-requested-with') == 'XMLHttpRequest'

        or request.content_type == 'application/json'

    ):



        return JsonResponse(

            {'message': 'Logged out successfully'}

        )



    return redirect('home')





@login_required

def dashboard_view(request):

    """Smart Dashboard Routing: Admin vs Distributor"""



    if not (

        request.user.is_staff

        or request.user.is_superuser

    ):



        DistributorProfile.objects.get_or_create(

            user=request.user,

            defaults={

                'phone': '+1 555-019-8842',

                'company_name': (

                    f"{request.user.first_name or request.user.username} "

                    f"Wholesale Logistics"

                ),

                'distributor_id': f"DIST-{random.randint(1000, 9999)}",

            }

        )



        return redirect('distributor_dashboard')



    return render(

        request,

        'accounts/dashboard.html',

        {'user': request.user}

    )





@login_required

def distributor_dashboard_view(request):

    """Distributor Logistics Portal Dashboard View"""



    return render(

        request,

        'accounts/distributor_dashboard.html',

        {'user': request.user}

    )





def forgot_password_view(request):



    return render(

        request,

        'accounts/forgot_password.html'

    )





def portal_hub_view(request):



    return render(

        request,

        'accounts/portal_hub.html'

    )





def admin_register_view(request):

    """Admin Governance Registration Form View"""



    if (

        request.user.is_authenticated

        and (

            request.user.is_staff

            or request.user.is_superuser

        )

    ):



        return redirect('dashboard')



    return render(

        request,

        'accounts/admin_register.html'

    )





@login_required

def distributor_profile_view(request):

    """Distributor Profile View: Displays and updates distributor details."""



    user = request.user



    profile, created = DistributorProfile.objects.get_or_create(

        user=user,

        defaults={

            'phone': '+1 555-019-8842',

            'company_name': (

                f"{user.first_name or user.username} "

                f"Wholesale Solutions"

            ),

            'distributor_id': f"DIST-{random.randint(1000, 9999)}",

        }

    )



    if request.method == 'POST':



        form = DistributorProfileForm(

            request.POST,

            user=user

        )



        if form.is_valid():



            full_name = form.cleaned_data['full_name']

            email = form.cleaned_data['email']

            phone = form.cleaned_data['phone']

            company_name = form.cleaned_data.get(

                'company_name',

                ''

            )



            name_parts = full_name.strip().split(' ', 1)



            user.first_name = name_parts[0]

            user.last_name = (

                name_parts[1]

                if len(name_parts) > 1

                else ''

            )



            user.email = email

            user.save()



            profile.phone = phone

            profile.company_name = company_name

            profile.save()



            messages.success(

                request,

                "Your Distributor Profile has been updated successfully!"

            )



            return redirect('distributor_profile')



        else:



            messages.error(

                request,

                "Please resolve the errors below to update your profile."

            )



    else:



        initial_data = {

            'full_name': user.get_full_name() or user.username,

            'email': user.email,

            'phone': profile.phone,

            'company_name': profile.company_name,

        }



        form = DistributorProfileForm(

            initial=initial_data,

            user=user

        )



    context = {

        'user': user,

        'profile': profile,

        'form': form,

    }



    return render(

        request,

        'accounts/distributor_profile.html',

        context

    )





@csrf_exempt

def api_distributor_profile_view(request):

    """API Endpoint for fetching and updating Distributor Profile details via JSON."""



    if not request.user.is_authenticated:



        return JsonResponse(

            {'error': 'Authentication required'},

            status=401

        )



    user = request.user



    profile, _ = DistributorProfile.objects.get_or_create(

        user=user,

        defaults={

            'phone': '+1 555-019-8842',

            'company_name': (

                f"{user.first_name or user.username} "

                f"Wholesale Solutions"

            ),

            'distributor_id': f"DIST-{random.randint(1000, 9999)}",

        }

    )



    if request.method in ['POST', 'PUT']:



        try:

            data = json.loads(request.body)



        except (json.JSONDecodeError, TypeError):

            data = request.POST



        form = DistributorProfileForm(

            data,

            user=user

        )



        if form.is_valid():



            full_name = form.cleaned_data['full_name']

            email = form.cleaned_data['email']

            phone = form.cleaned_data['phone']

            company_name = form.cleaned_data.get(

                'company_name',

                ''

            )



            name_parts = full_name.strip().split(' ', 1)



            user.first_name = name_parts[0]

            user.last_name = (

                name_parts[1]

                if len(name_parts) > 1

                else ''

            )



            user.email = email

            user.save()



            profile.phone = phone

            profile.company_name = company_name

            profile.save()



            return JsonResponse(

                {

                    'message': 'Distributor profile updated successfully',

                    'profile': {

                        'username': user.username,

                        'full_name': (

                            user.get_full_name()

                            or user.username

                        ),

                        'first_name': user.first_name,

                        'last_name': user.last_name,

                        'email': user.email,

                        'phone': profile.phone,

                        'company_name': profile.company_name,

                        'distributor_id': profile.distributor_id,

                        'credit_limit': str(profile.credit_limit),

                        'is_verified': profile.is_verified,

                        'created_at': (

                            profile.created_at.strftime(

                                '%Y-%m-%d %H:%M:%S'

                            )

                            if profile.created_at

                            else ''

                        ),

                    }

                },

                status=200

            )



        else:



            errors = {

                field: [str(e) for e in err_list]

                for field, err_list in form.errors.items()

            }



            return JsonResponse(

                {

                    'error': 'Validation failed',

                    'details': errors

                },

                status=400

            )



    return JsonResponse(

        {

            'user_id': user.id,

            'username': user.username,

            'full_name': (

                user.get_full_name()

                or user.username

            ),

            'first_name': user.first_name,

            'last_name': user.last_name,

            'email': user.email,

            'phone': profile.phone,

            'company_name': profile.company_name,

            'distributor_id': profile.distributor_id,

            'credit_limit': str(profile.credit_limit),

            'is_verified': profile.is_verified,

            'created_at': (

                profile.created_at.strftime(

                    '%Y-%m-%d %H:%M:%S'

                )

                if profile.created_at

                else ''

            ),

        },

        status=200

    )

# ============================================================

# ADMIN REPORTS

# ============================================================



@login_required

def reports_view(request):
    """
    Dedicated Admin Reports Section.

    Existing report functionality is preserved:
    - Today
    - Last 7 Days
    - Last 30 Days
    - Last 90 Days
    - All Time

    Added:
    - Custom From Date / To Date invoice filtering
    - Total invoice count for selected range
    - Amount collected for selected range
    """

    if not (
        request.user.is_staff
        or request.user.is_superuser
    ):
        return redirect('distributor_dashboard')

    period = request.GET.get('period', '30')
    today = timezone.localdate()

    if period == 'today':
        start_date = today
        end_date = today
        period_label = "Today"

    elif period == '7':
        start_date = today - timedelta(days=6)
        end_date = today
        period_label = "Last 7 Days"

    elif period == '30':
        start_date = today - timedelta(days=29)
        end_date = today
        period_label = "Last 30 Days"

    elif period == '90':
        start_date = today - timedelta(days=89)
        end_date = today
        period_label = "Last 90 Days"

    elif period == 'all':
        start_date = None
        end_date = today
        period_label = "All Time"

    else:
        period = '30'
        start_date = today - timedelta(days=29)
        end_date = today
        period_label = "Last 30 Days"

    # NEW: custom invoice date range
    custom_start_date = request.GET.get(
        'start_date',
        ''
    ).strip()

    custom_end_date = request.GET.get(
        'end_date',
        ''
    ).strip()

    date_error = ''
    custom_range_active = False

    if custom_start_date or custom_end_date:

        if not custom_start_date or not custom_end_date:
            date_error = (
                "Please select both From Date and To Date."
            )

        else:
            try:
                selected_start_date = date.fromisoformat(
                    custom_start_date
                )

                selected_end_date = date.fromisoformat(
                    custom_end_date
                )

                if selected_end_date < selected_start_date:
                    date_error = (
                        "To Date cannot be earlier than From Date."
                    )

                else:
                    start_date = selected_start_date
                    end_date = selected_end_date
                    custom_range_active = True

                    period_label = (
                        f"{selected_start_date.strftime('%d %b %Y')}"
                        f" → "
                        f"{selected_end_date.strftime('%d %b %Y')}"
                    )

            except ValueError:
                date_error = "Please enter valid dates."

    invoices = Invoice.objects.all()

    if start_date is not None:
        invoices = invoices.filter(
            invoice_date__gte=start_date
        )

    if end_date is not None:
        invoices = invoices.filter(
            invoice_date__lte=end_date
        )

    invoice_stats = invoices.aggregate(
        total_revenue=Sum('grand_total'),
        total_tax=Sum('tax_amount'),
        total_paid=Sum('amount_paid'),
        total_discount=Sum('discount_amount'),
        invoice_count=Count('id'),
    )

    total_revenue = (
        invoice_stats['total_revenue']
        or Decimal('0.00')
    )

    total_tax = (
        invoice_stats['total_tax']
        or Decimal('0.00')
    )

    total_paid = (
        invoice_stats['total_paid']
        or Decimal('0.00')
    )

    total_discount = (
        invoice_stats['total_discount']
        or Decimal('0.00')
    )

    invoice_count = (
        invoice_stats['invoice_count']
        or 0
    )

    outstanding_amount = total_revenue - total_paid

    status_report = []

    for status_code, status_name in Invoice.STATUS_CHOICES:

        count = invoices.filter(
            status=status_code
        ).count()

        status_report.append(
            {
                'code': status_code,
                'name': status_name,
                'count': count,
            }
        )

    products = Product.objects.all()

    total_products = products.count()

    active_products = products.filter(
        is_active=True
    ).count()

    inactive_products = products.filter(
        is_active=False
    ).count()

    low_stock_products = products.filter(
        stock__gt=0,
        stock__lte=models.F('min_stock_level')
    ).count()

    out_of_stock_products = products.filter(
        stock__lte=0
    ).count()

    inventory_value = sum(
        (
            product.price * product.stock
            for product in products
        ),
        Decimal('0.00')
    )

    total_customers = Customer.objects.count()

    active_customers = Customer.objects.filter(
        is_active=True
    ).count()

    inactive_customers = Customer.objects.filter(
        is_active=False
    ).count()

    total_outstanding_customer_balance = (
        Customer.objects.aggregate(
            total=Sum('outstanding_balance')
        )['total']
        or Decimal('0.00')
    )

    top_products = (
        InvoiceItem.objects
        .filter(invoice__in=invoices)
        .values(
            'product__name',
            'product__sku'
        )
        .annotate(
            quantity_sold=Sum('quantity'),
            sales_value=Sum('total_amount')
        )
        .order_by('-sales_value')[:5]
    )

    top_customers = (
        invoices
        .values(
            'customer__name',
            'customer__company_name'
        )
        .annotate(
            invoice_count=Count('id'),
            total_value=Sum('grand_total')
        )
        .order_by('-total_value')[:5]
    )

    recent_invoices = invoices.select_related(
        'customer'
    ).order_by(
        '-created_at'
    )[:10]

    low_stock_list = (
        products
        .filter(
            stock__lte=models.F('min_stock_level')
        )
        .order_by('stock')[:10]
    )

    context = {
        'period': period,
        'period_label': period_label,
        'today': today,

        # NEW custom report fields
        'custom_start_date': custom_start_date,
        'custom_end_date': custom_end_date,
        'date_error': date_error,
        'custom_range_active': custom_range_active,

        # Required new results
        'total_invoice_count': invoice_count,
        'amount_collected': total_paid,

        # Existing invoice data
        'invoice_count': invoice_count,
        'total_revenue': total_revenue,
        'total_tax': total_tax,
        'total_paid': total_paid,
        'total_discount': total_discount,
        'outstanding_amount': outstanding_amount,
        'status_report': status_report,

        # Products
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'inventory_value': inventory_value,

        # Customers
        'total_customers': total_customers,
        'active_customers': active_customers,
        'inactive_customers': inactive_customers,
        'total_outstanding_customer_balance': (
            total_outstanding_customer_balance
        ),

        # Lists
        'top_products': top_products,
        'top_customers': top_customers,
        'recent_invoices': recent_invoices,
        'low_stock_list': low_stock_list,
    }

    return render(
        request,
        'accounts/reports.html',
        context
    )
