from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .forms import RegistrationForm
from .serializers import RegisterSerializer, UserSerializer

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
