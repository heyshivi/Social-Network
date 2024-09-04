from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from .models import User, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer
from django.db.models import Q
from datetime import datetime, timedelta

class UserSignupView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response(
                {"message": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {"message": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(email=email, password=password)
        serializer = UserSerializer(user)
        return Response(
            {"message": "User created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )

class UserLoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        
        if user is not None:
            login(request, user)
            return Response(
                {"message": "Logged in successfully"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"message": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

class UserSearchView(APIView):
    def get(self, request, *args, **kwargs):
        search_keyword = request.query_params.get('q', '')
        if not search_keyword:
            return Response(
                {"message": "Search keyword is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = User.objects.filter(
            Q(email__icontains=search_keyword) |
            Q(first_name__icontains=search_keyword) |
            Q(last_name__icontains=search_keyword)
        ).distinct()
        
        paginator = Paginator(queryset, 10)  # 10 users per page
        page_number = request.query_params.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        serializer = UserSerializer(page_obj, many=True)
        return Response(
            {"message": "Search results", "data": serializer.data, "page": page_number, "total_pages": paginator.num_pages},
            status=status.HTTP_200_OK
        )

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        to_user_id = request.data.get('to_user')
        if not to_user_id:
            return Response(
                {"message": "Recipient user ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        to_user = User.objects.filter(id=to_user_id).first()
        if not to_user:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Rate limit: No more than 3 requests per minute
        time_limit = datetime.now() - timedelta(minutes=1)
        recent_requests = FriendRequest.objects.filter(
            from_user=request.user,
            created_at__gte=time_limit
        )
        if recent_requests.count() >= 3:
            return Response(
                {"message": "Too many friend requests sent. Please wait a minute before trying again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        existing_request = FriendRequest.objects.filter(
            from_user=request.user,
            to_user=to_user,
            accepted=False,
            rejected=False
        ).first()

        if existing_request:
            return Response(
                {"message": "Friend request already sent"},
                status=status.HTTP_400_BAD_REQUEST
            )

        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return Response(
            {"message": "Friend request sent successfully"},
            status=status.HTTP_201_CREATED
        )

class FriendRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        action = request.data.get('action')
        request_id = request.data.get('request_id')
        if action not in ['accept', 'reject']:
            return Response(
                {"message": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        friend_request = FriendRequest.objects.filter(id=request_id, to_user=request.user).first()
        if not friend_request:
            return Response(
                {"message": "Friend request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'accept':
            friend_request.accepted = True
            friend_request.save()
            return Response(
                {"message": "Friend request accepted"},
                status=status.HTTP_200_OK
            )
        elif action == 'reject':
            friend_request.rejected = True
            friend_request.save()
            return Response(
                {"message": "Friend request rejected"},
                status=status.HTTP_200_OK
            )

class FriendListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        friends = User.objects.filter(
            id__in=FriendRequest.objects.filter(from_user=request.user, accepted=True).values('to_user')
        )
        serializer = UserSerializer(friends, many=True)
        return Response(
            {"message": "Friend list retrieved successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )
