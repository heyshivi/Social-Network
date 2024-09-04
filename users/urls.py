from django.urls import path
from .views import UserSignupView, UserLoginView, UserSearchView, FriendRequestView, FriendRequestActionView, FriendListView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='user_signup'),
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('search/', UserSearchView.as_view(), name='user_search'),
    path('friend-request/', FriendRequestView.as_view(), name='friend_request'),
    path('friend-request/action/', FriendRequestActionView.as_view(), name='friend_request_action'),
    path('friends/', FriendListView.as_view(), name='friends_list'),
]
