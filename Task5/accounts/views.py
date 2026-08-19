import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .forms import LoginForm, DistributorLoginForm, DistributorRegistrationForm
from .models import OTPCode

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
        return redirect('dashboard')

    if request.method == 'POST':
        form = DistributorLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            next_url = request.GET.get('next') or 'dashboard'
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

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            messages.success(request, f"Distributor account created successfully! Welcome, {first_name}. Please sign in.")
            return redirect('distributor_login')
        else:
            messages.error(request, "Please resolve the validation errors below.")
    else:
        form = DistributorRegistrationForm()

    return render(request, 'accounts/distributor_register.html', {'form': form})

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

@require_http_methods(["POST"])
def api_request_otp_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        data = request.POST

    email = data.get('email') or data.get('username')
    if not email:
        return JsonResponse({'error': 'Email or username is required'}, status=400)

    otp = OTPCode.generate_otp(email)
    return JsonResponse({
        'message': 'OTP generated successfully',
        'email': email,
        'otp': otp.code
    }, status=200)

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
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html', {'user': request.user})

def forgot_password_view(request):
    return render(request, 'accounts/forgot_password.html')

def portal_hub_view(request):
    return render(request, 'accounts/portal_hub.html')
