import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import DistributorRegistrationForm
from .models import DistributorProfile

def distributor_register_view(request):
    """
    Handles GET and POST requests for Distributor Registration.
    Creates User record, DistributorProfile, and logs the user in upon success.
    """
    if request.user.is_authenticated:
        return redirect('distributor_dashboard')

    if request.method == 'POST':
        form = DistributorRegistrationForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            company_name = form.cleaned_data.get('company_name', '')
            password = form.cleaned_data['password']

            # Generate Username from email or name
            username = email.split('@')[0] + f"{random.randint(100, 999)}"
            
            # Split full name into first and last name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Create User Object
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Generate unique Distributor Tracking ID
            distributor_id = f"DIST-{random.randint(1000, 9999)}"

            # Create Distributor Profile
            profile = DistributorProfile.objects.create(
                user=user,
                phone=phone,
                company_name=company_name or f"{first_name} Logistics",
                distributor_id=distributor_id
            )

            messages.success(request, f"Distributor account created successfully! Welcome, {first_name}.")
            
            # Log in newly registered distributor
            login(request, user)
            return redirect('distributor_login')
        else:
            messages.error(request, "Please fix the errors in the form before submitting.")
    else:
        form = DistributorRegistrationForm()

    return render(request, 'accounts/distributor_register.html', {'form': form})
