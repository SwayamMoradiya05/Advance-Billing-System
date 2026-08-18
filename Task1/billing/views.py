from django.shortcuts import render

def index(request):
    context = {
        'title': 'Advance Billing System',
        'message': 'Django project successfully configured with SQLite3, static files, and billing app!',
    }
    return render(request, 'billing/index.html', context)
