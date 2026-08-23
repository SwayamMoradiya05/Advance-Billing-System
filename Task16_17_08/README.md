# Advance Billing System (ABS)

Enterprise wholesale billing, distributor management, and customer directory web application built with Django and Bootstrap 5.

---

## 🌟 Key Features

1. **Role-Separated Portals & Authentication**:
   - Admin Governance Suite with system metrics, QR invoice generator, and credit ledger.
   - Distributor Logistics Portal with stock intake tracker and credit line utilization.
   - Secure Login, Registration, and Password Reset workflows.

2. **Customer Directory & Account Management**:
   - Customer table with search bar, multi-field search (Name, Email, Phone, Code, City, Tax ID).
   - Status filtering (Active / Inactive) and dynamic sorting.
   - Full CRUD operations and REST API endpoints (`/customers/api/customers/`).

3. **Responsive Dark UI**:
   - High-contrast, modern UI built with Bootstrap 5 and custom CSS styles.
   - Interactive live client-side search alongside server-side GET filtering.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Installation & Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (Optional)
python manage.py createsuperuser

# Run local development server
python manage.py runserver
```

### 3. Running Unit Tests
```bash
python manage.py test
```

---

## 📁 Project Structure

```
.
├── accounts/          # Authentication & Distributor Profile App
├── customers/         # Customer Directory, CRUD, and REST API App
├── core/              # Django Project Settings & Root Routing
├── templates/         # Centralized HTML Templates
├── css/               # Custom Stylesheets
├── js/                # Client-Side Scripts & Validation
├── db.sqlite3         # SQLite Database
├── manage.py          # Django Management Script
├── requirements.txt   # Python Package Dependencies
└── README.md          # Documentation
```
