from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .forms import RegistrationForm, LoginForm
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

class RegisterView(View):
    """
    Web View to render and process the user registration page.
    """
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Welcome {user.first_name}! Your {user.profile.get_role_display()} account has been created.")
            login(request, user)
            return redirect('accounts:dashboard')
        return render(request, self.template_name, {'form': form})


class RegisterAPIView(APIView):
    """
    API endpoint to register a new user (Customer or Parking Provider).
    POST /api/auth/register/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            refresh['role'] = user.profile.role

            user_data = UserSerializer(user).data
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": user_data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "message": "Registration failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# ─── Login Views ────────────────────────────────────────────────────────────

class LoginView(View):
    """
    Web View to render and process the login page.
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class LoginAPIView(APIView):
    """
    API endpoint to log in and obtain JWT tokens.
    POST /api/auth/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            refresh['role'] = user.profile.role

            user_data = UserSerializer(user).data
            return Response(
                {
                    "message": "Login successful.",
                    "user": user_data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "message": "Login failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutAPIView(APIView):
    """
    API endpoint to blacklist a refresh token on logout.
    POST /api/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"message": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    """
    Protected API endpoint to view and update user profile.
    GET/PUT /api/auth/profile/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        user = request.user
        # Only allow safe profile field updates
        first_name = request.data.get('first_name', user.first_name)
        last_name = request.data.get('last_name', user.last_name)
        phone_number = request.data.get('phone_number', user.profile.phone_number)

        user.first_name = first_name.strip()
        user.last_name = last_name.strip()
        user.save()

        user.profile.phone_number = phone_number.strip()
        user.profile.save()

        serializer = UserSerializer(user)
        return Response(
            {"message": "Profile updated successfully.", "user": serializer.data},
            status=status.HTTP_200_OK
        )


# ─── Web UI Protected Views ──────────────────────────────────────────────────

class DashboardView(View):
    """
    Protected dashboard view — redirects to login if unauthenticated.
    """
    template_name = 'accounts/dashboard.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next=/dashboard/')
        return render(request, self.template_name, {'user': request.user})


class ProfileView(View):
    """
    Protected profile view — redirects to login if unauthenticated.
    """
    template_name = 'accounts/profile.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next=/profile/')
        return render(request, self.template_name, {'user': request.user})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next=/profile/')
        user = request.user
        first_name = request.POST.get('first_name', user.first_name).strip()
        last_name = request.POST.get('last_name', user.last_name).strip()
        phone_number = request.POST.get('phone_number', user.profile.phone_number).strip()

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()

        user.profile.phone_number = phone_number
        user.profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('accounts:profile')


class LogoutView(View):
    """
    Web logout view — invalidates Django session.
    """
    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('accounts:login')
