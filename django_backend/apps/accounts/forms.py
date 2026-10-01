from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from .models import UserProfile, UserRole

class RegistrationForm(forms.Form):
    """
    Registration form supporting Customer and Parking Provider accounts.
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': 'First name',
            'id': 'id_first_name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': 'Last name',
            'id': 'id_last_name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': 'name@example.com',
            'id': 'id_email'
        })
    )
    role = forms.ChoiceField(
        choices=UserRole.choices,
        initial=UserRole.CUSTOMER,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'id': 'id_role'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': '••••••••',
            'id': 'id_password'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': '••••••••',
            'id': 'id_confirm_password'
        })
    )

    def clean_first_name(self):
        return self.cleaned_data.get('first_name', '').strip()

    def clean_last_name(self):
        return self.cleaned_data.get('last_name', '').strip()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                dummy_user = User(
                    username=cleaned_data.get('email', ''),
                    email=cleaned_data.get('email', ''),
                    first_name=cleaned_data.get('first_name', ''),
                    last_name=cleaned_data.get('last_name', '')
                )
                try:
                    validate_password(password, user=dummy_user)
                except exceptions.ValidationError as error:
                    for msg in error.messages:
                        self.add_error('password', msg)

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=cleaned_data['password'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name']
        )
        UserProfile.objects.create(
            user=user,
            role=cleaned_data['role']
        )
        return user


class LoginForm(forms.Form):
    """
    Login form with email and password.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': 'name@example.com',
            'id': 'id_email',
            'autofocus': 'autofocus'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False, attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all',
            'placeholder': '••••••••',
            'id': 'id_password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').lower().strip()
        password = cleaned_data.get('password')

        if email and password:
            from django.contrib.auth.models import User
            user = (
                User.objects.filter(email__iexact=email).first()
                or User.objects.filter(username__iexact=email).first()
            )
            if not user or not user.check_password(password):
                raise forms.ValidationError("Invalid email or password. Please try again.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            self._user = user
        return cleaned_data

    def get_user(self):
        return self._user

