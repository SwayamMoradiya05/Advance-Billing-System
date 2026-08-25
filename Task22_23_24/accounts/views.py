import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .forms import LoginForm, DistributorLoginForm, DistributorRegistrationForm, DistributorProfileForm
from .models import OTPCode, DistributorProfile

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

    return render(request, 'accounts/distributor_login.html', {'form': form})

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

            # Create User in database
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create Distributor Profile in database
            distributor_id = f"DIST-{random.randint(1000, 9999)}"
            profile = DistributorProfile.objects.create(
                user=user,
                phone=phone,
                company_name=company_name or f"{first_name} Logistics",
                distributor_id=distributor_id
            )

            messages.success(request, f"Distributor account created successfully! Welcome, {first_name}. Please sign in.")
            return redirect('distributor_login')
        else:
            messages.error(request, "Please resolve the validation errors below.")
    else:
        form = DistributorRegistrationForm()

    return render(request, 'accounts/distributor_register.html', {'form': form})

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
        profile = DistributorProfile.objects.create(
            user=user,
            phone=phone,
            company_name=company_name or f"{first_name} Logistics",
            distributor_id=distributor_id
        )

        return JsonResponse({
            'message': f"Distributor account created successfully! Welcome, {first_name}. Please sign in.",
            'distributor_id': distributor_id,
            'redirect_url': '/distributor-login/'
        }, status=201)
    else:
        errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
        return JsonResponse({'error': 'Validation failed', 'details': errors}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def api_login_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return JsonResponse({'error': 'Username and password are required'}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        try:
            user_obj = User.objects.get(username=username)
            if user_obj.check_password(password) and not user_obj.is_active:
                return JsonResponse({'error': 'Account is disabled'}, status=403)
        except User.DoesNotExist:
            pass
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    login(request, user)
    return JsonResponse({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.first_name or user.username,
            'email': user.email,
        }
    }, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def api_request_otp_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        data = request.POST

    raw_input = data.get('email') or data.get('username')
    if not raw_input:
        return JsonResponse({'error': 'Email or username is required'}, status=400)

    clean_input = str(raw_input).strip()

    # Resolve target recipient email from User model if username was passed
    target_email = clean_input
    user_obj = User.objects.filter(Q(email__iexact=clean_input) | Q(username__iexact=clean_input)).first()
    if user_obj and user_obj.email:
        target_email = user_obj.email

    otp = OTPCode.generate_otp(target_email)

    email_sent = False
    try:
        if '@' in target_email:
            send_mail(
                subject='Your OTP Code - Advance Billing System',
                message=f'Your One-Time Password (OTP) for account reset is: {otp.code}\n\nThis code is valid for 10 minutes.',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'moradiyaswayam@gmail.com'),
                recipient_list=[target_email],
                fail_silently=False,
            )
            email_sent = True
    except Exception as e:
        print(f"SMTP Email Error: {e}")

    return JsonResponse({
        'message': 'OTP generated successfully',
        'email': target_email,
        'otp': otp.code,
        'email_sent': email_sent
    }, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def api_verify_otp_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        data = request.POST

    email = data.get('email') or data.get('username')
    code = data.get('code') or data.get('otp')
    new_password = data.get('new_password')

    if not email or not code:
        return JsonResponse({'error': 'Email and OTP code are required'}, status=400)

    if not OTPCode.validate_otp(email, str(code).strip()):
        return JsonResponse({'error': 'Invalid or expired OTP'}, status=400)

    if new_password:
        user = User.objects.filter(Q(email=email) | Q(username=email)).first()
        if user:
            user.set_password(new_password)
            user.save()

    return JsonResponse({'message': 'OTP verified successfully'}, status=200)

def logout_view(request):
    logout(request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'message': 'Logged out successfully'})
    return redirect('home')

@login_required
def dashboard_view(request):
    """Smart Dashboard Routing: Admin vs Distributor"""
    if not (request.user.is_staff or request.user.is_superuser):
        # Auto-create DistributorProfile if missing for non-admin user
        DistributorProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'phone': '+1 555-019-8842',
                'company_name': f"{request.user.first_name or request.user.username} Wholesale Logistics",
                'distributor_id': f"DIST-{random.randint(1000, 9999)}",
            }
        )
        return redirect('distributor_dashboard')
    return render(request, 'accounts/dashboard.html', {'user': request.user})

@login_required
def distributor_dashboard_view(request):
    """Distributor Logistics Portal Dashboard View"""
    return render(request, 'accounts/distributor_dashboard.html', {'user': request.user})

def forgot_password_view(request):
    return render(request, 'accounts/forgot_password.html')

def portal_hub_view(request):
    return render(request, 'accounts/portal_hub.html')

@login_required
def distributor_profile_view(request):
    """Distributor Profile View: Displays and updates distributor details."""
    user = request.user
    
    # Ensure user has a DistributorProfile (create one if missing)
    profile, created = DistributorProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '+1 555-019-8842',
            'company_name': f"{user.first_name or user.username} Wholesale Solutions",
            'distributor_id': f"DIST-{random.randint(1000, 9999)}",
        }
    )

    if request.method == 'POST':
        form = DistributorProfileForm(request.POST, user=user)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            company_name = form.cleaned_data.get('company_name', '')

            # Parse full name
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.email = email
            user.save()

            # Update Profile
            profile.phone = phone
            profile.company_name = company_name
            profile.save()

            messages.success(request, "Your Distributor Profile has been updated successfully!")
            return redirect('distributor_profile')
        else:
            messages.error(request, "Please resolve the errors below to update your profile.")
    else:
        initial_data = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'phone': profile.phone,
            'company_name': profile.company_name,
        }
        form = DistributorProfileForm(initial=initial_data, user=user)

    context = {
        'user': user,
        'profile': profile,
        'form': form,
    }
    return render(request, 'accounts/distributor_profile.html', context)


@csrf_exempt
def api_distributor_profile_view(request):
    """API Endpoint for fetching and updating Distributor Profile details via JSON."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    user = request.user
    profile, _ = DistributorProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '+1 555-019-8842',
            'company_name': f"{user.first_name or user.username} Wholesale Solutions",
            'distributor_id': f"DIST-{random.randint(1000, 9999)}",
        }
    )

    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            data = request.POST

        form = DistributorProfileForm(data, user=user)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            company_name = form.cleaned_data.get('company_name', '')

            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.email = email
            user.save()

            profile.phone = phone
            profile.company_name = company_name
            profile.save()

            return JsonResponse({
                'message': 'Distributor profile updated successfully',
                'profile': {
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone': profile.phone,
                    'company_name': profile.company_name,
                    'distributor_id': profile.distributor_id,
                    'credit_limit': str(profile.credit_limit),
                    'is_verified': profile.is_verified,
                    'created_at': profile.created_at.strftime('%Y-%m-%d %H:%M:%S') if profile.created_at else '',
                }
            }, status=200)
        else:
            errors = {field: [str(e) for e in err_list] for field, err_list in form.errors.items()}
            return JsonResponse({'error': 'Validation failed', 'details': errors}, status=400)

    # GET Request
    return JsonResponse({
        'user_id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': profile.phone,
        'company_name': profile.company_name,
        'distributor_id': profile.distributor_id,
        'credit_limit': str(profile.credit_limit),
        'is_verified': profile.is_verified,
        'created_at': profile.created_at.strftime('%Y-%m-%d %H:%M:%S') if profile.created_at else '',
    }, status=200)

