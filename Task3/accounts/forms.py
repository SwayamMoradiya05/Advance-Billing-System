from django import forms
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user_obj = User.objects.get(username=username)
                    if user_obj.check_password(password) and not user_obj.is_active:
                        raise forms.ValidationError('This user account is inactive.')
                except User.DoesNotExist:
                    pass
                raise forms.ValidationError('Invalid username or password.')

            cleaned_data['user'] = user

        return cleaned_data
