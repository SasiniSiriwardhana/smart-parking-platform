from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer

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
