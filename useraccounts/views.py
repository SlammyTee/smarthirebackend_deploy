import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from .utils import generate_random_password
from useraccounts.permissions import IsAdmin
from .models import User
 


@api_view(['POST'])
@permission_classes([AllowAny])
def register_candidate(request):
    try:
        data = request.data

        required_fields = ['username', 'email', 'password', 'fullName']
        if not all(field in data for field in required_fields):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=data['email']).exists():
            return Response({'error': 'Email already registered'}, status=400)

        if User.objects.filter(username=data['username']).exists():
            return Response({'error': 'Username already taken'}, status=400)

        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            username=data['username'],
            fullname=data['fullName'],
            role='candidate'
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "detail": "Registration successful",
            "email": user.email,
            "pk": user.pk,
            "access": access_token,
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=400)


# ✅ FIXED LOGIN VIEW
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "detail": "Login successful",
            'access': access_token,
            'refresh': str(refresh),
            "pk": user.pk,
            "email": user.email,
            "role": user.role,
            "must_change_password": user.must_change_password
        }, status=status.HTTP_200_OK)

    


    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    try:
        refresh_token_str = request.COOKIES.get('refresh_token')

        if not refresh_token_str:
            return Response({'error': 'No refresh token'}, status=401)

        try:
            refresh = RefreshToken(refresh_token_str)
            access_token = str(refresh.access_token)
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=401)

        res = Response({'message': 'Token refreshed'}, status=200)

        res.set_cookie(
            'access',
            access_token,
            httponly=True,
            secure=True,
            samesite='None',
            max_age=60 * 60
        )

        return res

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout(request):
    res = Response({'message': 'Logout successful'}, status=200)

    res.delete_cookie('access_token')
    res.delete_cookie('refresh_token')

    return res


def get_user_from_cookie(request):
    token = request.COOKIES.get('access_token')

    if not token:
        raise AuthenticationFailed("Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")

    return payload


@api_view(["GET"])
@permission_classes([IsAdmin])
def get_system_users(request):
    users = User.objects.all().order_by("-date_joined")

    data = []

    for user in users:
        data.append({
            "id": user.id,
            "name": user.fullname,
            "email": user.email,
            "role": user.role if user.role else "No Role",
        })

    return Response({
        "success": True,
        "count": users.count(),
        "users": data
    })

@api_view(["GET"])
@permission_classes([IsAdmin])
def get_hr_users(request):
    hr_users = User.objects.filter(role="hr").order_by("-date_joined")

    data = []

    for user in hr_users:
        data.append({
            "id": user.id,
            "name": user.fullname,
            "email": user.email,
            "role": user.role if user.role else "No Role",
        })

    return Response({
        "success": True,
        "count": hr_users.count(),
        "users": data
    })


@api_view(["POST"])
@permission_classes([IsAdmin])
def create_hr_account(request):
    # This function can be used to create HR accounts, 
    # but it should be protected and only accessible by admins.
    try:
        email = request.data.get('email')
        fullname = request.data.get('name') 
        username = request.data.get('username')
        role = "hr"

        if not email or not fullname or not username:
            return Response({'error': 'Missing required fields'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=400)
        
        raw_password = generate_random_password(length=12)

        user = User.objects.create_user(
            email=email,
            password=raw_password,
            fullname=fullname,
            username=username,
            role=role
        )

        user.must_change_password = True
        user.save()

        send_mail(
            subject="Your HR Account Credentials",
            message=(
                f"Hello {fullname},\n\n"
                f"Your HR account has been created.\n\n"
                f"Email: {email}\n"
                f"Password: {raw_password}\n\n"
                f"You will be required to change your password after first login."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        return Response({'error': 'Missing required fields'}, status=400)
    
    return Response(
        {"message": "HR account created and email sent successfully"},
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def change_password(request):
    # This function can be used to allow users to change their password,
    # especially if they have the must_change_password flag set to True.
    user = request.user

    new_password = request.data.get('new_password')

    user.set_password(new_password)
    user.must_change_password = False
    user.save()

    return Response(
        {
            "success": True,
            "message": "Password changed successfully"
        }, status=status.HTTP_200_OK
    )

@api_view(["GET"])
@permission_classes([AllowAny])
def get_current_user(request):
    """
    Returns authenticated user details
    """

    user = request.user

    return Response(
        {
            "success": True,
            "user": {
                "id": user.id,
                "name": getattr(user, "fullname", user.username),
                "email": user.email,
                "role": user.role,
            },
        },
        status=status.HTTP_200_OK,
    )