from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from .models import UserProfile, UserRole

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('role', 'role_display', 'phone_number', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with embedded UserProfile.
    Exposes a top-level 'role' field for easy frontend consumption.
    """
    profile = UserProfileSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'role', 'profile')
        read_only_fields = ('id', 'username', 'is_staff', 'is_active')

    def get_role(self, obj):
        """Return the user's role string directly."""
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return None


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email, password, and role validation.
    """
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.CUSTOMER)
    phone_number = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'confirm_password', 'role', 'phone_number')

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(username__iexact=normalized_email).exists() or User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return normalized_email

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Apply Django's built-in password validators
        dummy_user = User(
            username=attrs.get('email'),
            email=attrs.get('email'),
            first_name=attrs.get('first_name'),
            last_name=attrs.get('last_name')
        )
        try:
            validate_password(password, user=dummy_user)
        except exceptions.ValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)})

        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        role = validated_data.get('role', UserRole.CUSTOMER)
        phone_number = validated_data.get('phone_number', '')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=phone_number
        )

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for validating login credentials and issuing JWT tokens.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        # Ensure user profile exists
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user, role=UserRole.CUSTOMER)

        attrs['user'] = user
        return attrs

