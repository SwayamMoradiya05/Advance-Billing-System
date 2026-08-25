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
