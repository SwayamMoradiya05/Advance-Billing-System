from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class LoginSerializer:
    def __init__(self, data):
        self.data = data
        self.errors = {}
        self.user = None

    def is_valid(self):
        username = self.data.get('username')
        password = self.data.get('password')

        if not username:
            self.errors['username'] = ['This field is required.']
        if not password:
            self.errors['password'] = ['This field is required.']

        if self.errors:
            return False

        user = authenticate(username=username, password=password)
        if user is None:
            try:
                user_obj = User.objects.get(username=username)
                if user_obj.check_password(password) and not user_obj.is_active:
                    self.errors['non_field_errors'] = ['User account is disabled.']
                    return False
            except User.DoesNotExist:
                pass
            self.errors['non_field_errors'] = ['Unable to log in with provided credentials.']
            return False

        self.user = user
        return True

class OTPRequestSerializer:
    def __init__(self, data):
        self.data = data
        self.errors = {}
        self.email = None

    def is_valid(self):
        email = self.data.get('email') or self.data.get('username')
        if not email:
            self.errors['email'] = ['Email or username is required.']
            return False
        self.email = email
        return True

class OTPVerifySerializer:
    def __init__(self, data):
        self.data = data
        self.errors = {}
        self.email = None
        self.code = None
        self.new_password = None

    def is_valid(self):
        email = self.data.get('email') or self.data.get('username')
        code = self.data.get('code') or self.data.get('otp')
        new_password = self.data.get('new_password')

        if not email:
            self.errors['email'] = ['Email is required.']
        if not code:
            self.errors['code'] = ['OTP code is required.']

        if self.errors:
            return False

        self.email = email
        self.code = str(code).strip()
        self.new_password = new_password
        return True


class AdminRegistrationSerializer:
    """
    Serializer / Validator for Admin User Registration API payloads.
    """
    def __init__(self, data):
        self.data = data
        self.errors = {}
        self.cleaned_data = {}

    def is_valid(self):
        import re
        username = str(self.data.get('username', '')).strip()
        email = str(self.data.get('email', '')).strip().lower()
        password = self.data.get('password')
        first_name = str(self.data.get('first_name', '')).strip()
        last_name = str(self.data.get('last_name', '')).strip()
        is_superuser = bool(self.data.get('is_superuser', False))

        if not username:
            self.errors['username'] = ['Username is required.']
        elif len(username) < 3:
            self.errors['username'] = ['Username must be at least 3 characters long.']
        elif User.objects.filter(username__iexact=username).exists():
            self.errors['username'] = ['A user with this username already exists.']

        if not email:
            self.errors['email'] = ['Email address is required.']
        else:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                self.errors['email'] = ['Please enter a valid email address format.']
            elif User.objects.filter(email__iexact=email).exists():
                self.errors['email'] = ['An account with this email address is already registered.']

        if not password:
            self.errors['password'] = ['Password is required.']
        elif len(password) < 8:
            self.errors['password'] = ['Password must be at least 8 characters long.']
        elif not (re.search(r'[A-Za-z]', password) and re.search(r'[0-9]', password)):
            self.errors['password'] = ['Password must contain a mix of letters and numbers.']

        if self.errors:
            return False

        self.cleaned_data = {
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'is_superuser': is_superuser,
        }
        return True
