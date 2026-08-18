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
